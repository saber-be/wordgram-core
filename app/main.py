import requests
from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
import datetime
from pymongo.errors import ServerSelectionTimeoutError
import pickle
import datetime
import pydantic_core
from instagrapi import Client
from pymongo import MongoClient
import os
import logging
from app.models.shop import Shop
from app.models.certificate import Certificate
from app.models.updateWebSiteRequest import updateWebSiteRequest
from app.api import log
from app.services.log_service import MongoHandler , FileHandler
from app.services.post_reader_service import PostReaderService
from app.services.kafka_service import KafkaService, KAFKA_TOPIC
from fastapi.middleware.cors import CORSMiddleware
import secrets


app = FastAPI()
app.include_router(log.router)
client = MongoClient(os.environ.get('MONGO_HOST'), int(os.environ.get('MONGO_PORT')))
db = client[os.environ.get('MONGO_DB')]


logging.basicConfig(level=logging.INFO)
mongo_handler = MongoHandler()
file_handler = FileHandler('logs')

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
mongo_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logging.getLogger().addHandler(mongo_handler)
logging.getLogger().addHandler(file_handler)

kafka_service = KafkaService()





@app.get("/")
def read_root():
    return {"Hello": os.environ.get('MONGO_HOST')}

# Add CORS middleware to allow OPTIONS request
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post('/register-shop', response_model=dict)
def register_shop(shop: Shop):
    if shop.shop_name == "" or shop.platform == "" \
            or shop.platform_url == "" or shop.redirect_url == "" \
            or shop.product_webhook_url == "" or shop.order_webhook_url == "" \
            or shop.instagram_username == "":
        return {'status': 'error', 'message': 'Please fill all the required fields'}

    # insert to mongodb
    collection = db['clients']
    try:
        message = 'Shop registered successfully'
        if collection.find_one({"instagram_username": shop.instagram_username}) is None:
            shop.created_at = datetime.datetime.now()
            shop.api_key = secrets.token_hex(16)
            print("Inserting to mongodb", shop.instagram_username)
            insert_data = shop.__dict__
            collection.insert_one(insert_data)
            data = insert_data
        else:
            message = 'Shop updated successfully'
            print("Updating to mongodb", shop.instagram_username)
            # update the document
            update_data = shop.__dict__
            freeze_columns = ['created_at', 'state', 'api_key']
            for column in freeze_columns:
                update_data.pop(column, None)
            collection.update_one(
                {"instagram_username": shop.instagram_username}, {"$set": update_data})
            data = collection.find_one(
                {"instagram_username": shop.instagram_username})
            data = {key: data[key] for key in data if key != "_id"}
        return {'status': 'success', 'message': message, 'data': data}
    except ServerSelectionTimeoutError:
        return {'status': 'error', 'message': 'Failed to connect to the MongoDB server'}


@app.post('/is-connect', response_model=dict)
def is_connect(certificate: Certificate):
    collection = db['clients']
    query_find = {
        "instagram_username": certificate.instagram_username, "state": certificate.state, "api_key": certificate.api_key}
    user = collection.find_one(query_find)
    if user is None:
        return {'status': 'error', 'message': 'Client not found'}
    data = {key: user[key] for key in user if key != "_id"}
    response = {'status': 'success',
                'success': True, 'message': 'Client found'}
    response.update(data)
    return response

@app.get('/fetch-from-instagram')
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

@app.post('/update-client-website')
def update_client_website(update_request: updateWebSiteRequest):
    # http://localhost:81/update-client-website?instagram_username=mosakbary
    # get posts from mongodb and update the client's website
    posts_collection = db['posts']
    client_collection = db['clients']
    instagram_username = update_request.instagram_username
    client = client_collection.find_one({"instagram_username": instagram_username})
    if client is None:
        return {'status': 'error', 'message': 'Client not found'}
    post_query = {"user.username": instagram_username}
    if update_request.SUK is not None:
        post_query["code"] = update_request.SUK
    posts = posts_collection.find(post_query)
    # loop through the posts and update the client's website
    print("Updating client website1")
    products = []
    for post in posts:
        print("Updating client website")       
        #  send request to the client's website
        url = client["product_webhook_url"]
        # url = "http://localhost:8082/wp-admin/admin-ajax.php?action=wordgram-product-hook"
        if update_request.force_update == False or ('published_at' in post and 'updated_at' in post and post["published_at"] and post["published_at"] >= post["updated_at"]):
            continue
        json_data = PostReaderService.instaToWordGramMapper(post, update_request)
        products.append(json_data)
        re = requests.post(url, json={"action": "addProduct", "products": [json_data]})
        if re.status_code == 200:
            posts_collection.update_one(
                {"instagram_id": post["instagram_id"]}, {"$set": {"published_at": datetime.datetime.now()}})
        print(re.text)
        
        
    return {'status': 'success', 'message': 'Client website updated successfully'}
    



@app.get('/fetch-all-posts')
def fetch_all_posts_from_all_accounts():
    # http://localhost:81/fetch-all-posts
    # fetch all posts from all client accounts
    collection = db['clients']
    clients = collection.find()
    for client in clients:
        sync_shop(client["instagram_username"])
    return {'status': 'success', 'message': 'All posts fetched successfully'}

@app.post("/produce/")
def produce_message(message: str):
    try:
        producer = kafka_service.kafka_producer()
        producer.send(KAFKA_TOPIC, message.encode('utf-8'))
        producer.flush()
        return {"status": "success", "message": "Message sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to produce message: {e}")
