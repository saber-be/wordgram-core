import datetime
import json
import logging
import time
import os
from pymongo import MongoClient
import requests
from app.services.kafka_service import KafkaService
from app.services.post_reader_service import PostReaderService
from app.services.log_service import MongoHandler , FileHandler
from app.models.updateWebSiteRequest import updateWebSiteRequest
logging.basicConfig(level=logging.INFO)
mongo_handler = MongoHandler()
file_handler = FileHandler('logs')

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
mongo_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logging.getLogger().addHandler(mongo_handler)
logging.getLogger().addHandler(file_handler)

kafka_service = KafkaService()
TOPIC_WP_UPDATER = os.getenv('TOPIC_WP_UPDATER')
client = MongoClient(os.environ.get('MONGO_HOST'), int(os.environ.get('MONGO_PORT')))
db = client[os.environ.get('MONGO_DB')]


def update_client_website(update_request: updateWebSiteRequest):
    # http://localhost:81/update-client-website?instagram_username=mosakbary
    # get posts from mongodb and update the client's website
    posts_collection = db['posts']
    client_collection = db['clients']
    instagram_username = update_request.instagram_username.lower()
    client = client_collection.find_one({"instagram_username": instagram_username, "disconnect_at": None})
    if client is None:
        logging.error("Client not found for "+instagram_username+" or client is disconnected")
        return {'status': 'error', 'message': 'Client not found'}
    post_query = {"user.username": instagram_username}
    if update_request.SKU is not None:
        post_query["code"] = update_request.SKU
    posts = posts_collection.find(post_query)
    # loop through the posts and update the client's website
    logging.info("Updating client "+instagram_username+" website")
    for post in posts:
        logging.info("Updating client website")       
        #  send request to the client's website
        url = client["product_webhook_url"]
        # url = "http://localhost:8082/wp-admin/admin-ajax.php?action=wordgram-product-hook"
        if (update_request.force_update == False and update_request.update_all_posts == False) and (update_request.SKU == None) and ('published_at' in post and 'updated_at' in post and post["published_at"] and post["published_at"] >= post["updated_at"]):
            logging.info("Post " + (post["code"] if "code" in post else post["_id"])+ " is already updated. Skipping...")
            continue
        json_data = PostReaderService.instaToWordGramMapper(post, update_request)
        logging.info(json_data)
       
        re = requests.post(url, json={"action": "addProduct", "products": [json_data]})
        if re.status_code == 200:
            posts_collection.update_one(
                {"instagram_id": post["instagram_id"]}, {"$set": {"published_at": datetime.datetime.now()}})
            logging.info(re.text)
        else:
            logging.error(re.text)
    
    logging.info("Client website updated successfully")
    return {'status': 'success', 'message': 'Client website updated successfully'}


while True:
    try:
        consumer = kafka_service.kafka_consumer(TOPIC_WP_UPDATER)
        break
    except Exception as e:
        logging.error("Kafka consumer failed to connect. Retrying...")
        logging.error(str(e))
        # Wait for 5 seconds before retrying
        time.sleep(5)
# Continuously listen for messages
logging.info("Starting consumer...")
try:
    for message in consumer:
        # json parse pessage into dict 
        logging.info("Message received:\n" + message.value.decode('utf-8'))
        message_dict = json.loads(message.value.decode('utf-8'))
        update_request_obj = updateWebSiteRequest(**message_dict)
        update_client_website(update_request_obj)
except json.JSONDecodeError as e:
    logging.error("Error parsing message: " + str(e))
except KeyboardInterrupt:
    logging.info("Consumer interrupted. Closing...")
finally:
    consumer.close()