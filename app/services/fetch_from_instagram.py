import json
import logging
import time
import os
import pickle
import datetime
import pydantic_core
from pymongo import MongoClient
from instagrapi import Client
from app.services.kafka_service import KafkaService, TOPIC_FETCH_FROM_INSTAGRAM
from app.services.log_service import MongoHandler , FileHandler

logging.basicConfig(level=logging.INFO)
mongo_handler = MongoHandler()
file_handler = FileHandler('logs')

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
mongo_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logging.getLogger().addHandler(mongo_handler)
logging.getLogger().addHandler(file_handler)

kafka_service = KafkaService()
client = MongoClient(os.environ.get('MONGO_HOST'), int(os.environ.get('MONGO_PORT')))
db = client[os.environ.get('MONGO_DB')]

def sync_shop(instagram_username: str):
    # http://localhost:81/sync-shop?instagram_username=mosakbary
    # http://localhost:81/fetch-from-instagram?instagram_username=59378186213
    # load c1 object from the pickle file
    ACCOUNT_USERNAME = os.environ.get('ACCOUNT_USERNAME')
    ACCOUNT_PASSWORD = os.environ.get('ACCOUNT_PASSWORD')
    collection = db['posts']
    cl = None
    try:
        # load c1 object from the pickle file
        with open('cl.pkl', 'rb') as f:
            cl = pickle.load(f)
    except:
        print("Logging in...")
        cl = Client()
        cl.login(ACCOUNT_USERNAME, ACCOUNT_PASSWORD)
        print("Logged in")
        with open('cl.pkl', 'wb') as f:
            pickle.dump(cl, f)
    
    user_id = instagram_username
    # if user_id is not a number, get the user_id from the username
    if not user_id.isdigit():
        user_id = cl.user_id_from_username(instagram_username)
    medias = cl.user_medias(user_id, 200)
    # store medias in mongodb
    for media in medias:
        json_data = media.dict()
        json_data["instagram_id"] = json_data["id"]
        json_data["instagram_user_id"] = user_id
        # loop through the json_data and convert pydontic objects to string
        for key in json_data:
            if isinstance(json_data[key], pydantic_core._pydantic_core.Url):
                print("URL found")
                json_data[key] = str(json_data[key])
        #  if instance of URL
        # set instagram_id unique in the collection
        json_data["instagram_id"] = json_data["id"]
        json_data["updated_at"] = datetime.datetime.now()
        old_data = collection.find_one({"instagram_id": json_data["instagram_id"]})
        # insert to mongodb
        if old_data is None:
            print("Inserting to mongodb")
            json_data["created_at"] = datetime.datetime.now()
            json_data["published_at"] = None
            try:
                collection.insert_one(json_data)
            except:
                print("Error inserting to mongodb")
        else:
            print("Updating to mongodb")
            # update the document
            excepted_keys = ['created_at', 'updated_at', 'taken_at', 'video_url', 'image_versions2', 'user']
            compared_keys = ['caption_text']
            changed_keys = []
            for key in json_data:
                if key in old_data and key not in excepted_keys and key in compared_keys and old_data[key] != json_data[key]:
                    changed_keys.append(key)
            if len(changed_keys) > 0:
                json_data['changed_keys'] = changed_keys
                collection.update_one(
                    {"instagram_id": json_data["instagram_id"]}, {"$set": json_data})

    return {'status': 'success', 'message': 'Shop synced successfully'}




while True:
    try:
        consumer = kafka_service.kafka_consumer(TOPIC_FETCH_FROM_INSTAGRAM)
        break
    except:
        logging.error("Kafka consumer failed to connect. Retrying...")
        # Wait for 5 seconds before retrying
        time.sleep(5)
# Continuously listen for messages
logging.info("Starting consumer...")
try:
    for message in consumer:
        # json parse pessage into dict 
        logging.info("Message received:\n" + message.value.decode('utf-8'))
        message_dict = json.loads(message.value.decode('utf-8'))
        instagram_username = message_dict['instagram_username']
        sync_shop(instagram_username)

except KeyboardInterrupt:
    logging.info("Consumer interrupted. Closing...")
finally:
    consumer.close()