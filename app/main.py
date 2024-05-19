import json
import requests
from fastapi import FastAPI, HTTPException, Query
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
from app.services.kafka_service import KafkaService
from app.services.proxy_service import ProxyService
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
TOPIC_WP_UPDATER = os.getenv('TOPIC_WP_UPDATER')
TOPIC_FETCH_FROM_INSTAGRAM = os.getenv('TOPIC_FETCH_FROM_INSTAGRAM')




@app.get("/")
async def read_root():
    return {"Hello": os.environ.get('MONGO_HOST')}

# Add CORS middleware to allow OPTIONS request
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post('/register-shop', response_model=dict)
async def register_shop(shop: Shop):
    if shop.shop_name == "" or shop.platform == "" \
            or shop.platform_url == "" or shop.redirect_url == "" \
            or shop.product_webhook_url == "" or shop.order_webhook_url == "" \
            or shop.instagram_username == "":
        return {'status': 'error', 'message': 'Please fill all the required fields'}

    # insert to mongodb
    collection = db['clients']
    default_values = {
        "instagram_sync_count": 0,
        "instagram_sync_max": 30,
        "daily_instagram_sync_count": 0,
        "daily_instagram_sync_max": 5,
        "website_update_count": 0,
        "website_update_max": 50,
        "daily_website_update_count": 0,
        "daily_website_update_max": 10
    }
    shop.instagram_username = shop.instagram_username.lower()
    try:
        message = 'Shop registered successfully'
        if collection.find_one({"instagram_username": shop.instagram_username}) is None:
            shop.created_at = datetime.datetime.now()
            shop.api_key = secrets.token_hex(16)
            print("Inserting to mongodb", shop.instagram_username)
            insert_data = shop.__dict__
            collection.insert_one(insert_data)
            data = collection.find_one(
                {"instagram_username": shop.instagram_username})
            data = {key: data[key] for key in data if key != "_id"}
        else:
            message = 'Shop updated successfully'
            print("Updating to mongodb", shop.instagram_username)
            # update the document
            update_data = shop.__dict__
            freeze_columns = ['created_at', 'state', 'api_key']
            for column in freeze_columns:
                update_data.pop(column, None)
            update_data["disconnect_at"] = None
            collection.update_one(
                {"instagram_username": shop.instagram_username}, {"$set": update_data})
            data = collection.find_one(
                {"instagram_username": shop.instagram_username})
            data = {key: data[key] for key in data if key != "_id"}
        
        # init default values if not exist in client collection else keep same value: 
        insert_default_values = {key: default_values[key] for key in default_values if key not in data}
        collection.update_one({"instagram_username": shop.instagram_username}, {"$set": insert_default_values})
        return {'status': 'success', 'message': message, 'data': data}
    except ServerSelectionTimeoutError:
        return {'status': 'error', 'message': 'Failed to connect to the MongoDB server'}


@app.post('/is-connect', response_model=dict)
async def is_connect(certificate: Certificate):
    collection = db['clients']
    query_find = {
        "instagram_username": certificate.instagram_username, "state": certificate.state, "api_key": certificate.api_key, "disconnect_at": None}
    user = collection.find_one(query_find)
    if user is None:
        return {'status': 'error', 'message': 'Client not found'}
    data = {key: user[key] for key in user if key != "_id"}
    response = {'status': 'success',
                'success': True, 'message': 'Client found'}
    response.update(data)
    return response

@app.post('/disconnect-shop', response_model=dict)
async def disconnect_shop(certificate: Certificate):
    collection = db['clients']
    query_find = {
        "instagram_username": certificate.instagram_username, "state": certificate.state, "api_key": certificate.api_key}
    user = collection.find_one(query_find)
    if user is None:
        return {'status': 'error', 'message': 'Client not found'}
    
    collection.update_one(query_find, {"$set": {"disconnect_at": datetime.datetime.now()}})
    data = {key: user[key] for key in user if key != "_id"}
    response = {'status': 'success', 'success': True, 'message': 'Client disconnected successfully'}
    response.update(data)
    return response

@app.post('/sync-shop', response_model=dict)
async def sync_shop(update_request: updateWebSiteRequest):
    collection = db['clients']
    logging.info('Request received to sync shop: ' + update_request.instagram_username)
    logging.info('Request is: ' + str(update_request))
    query_find = {
        "instagram_username": update_request.instagram_username.lower(), "state": update_request.state, "api_key": update_request.api_key}
    user = collection.find_one(query_find)
    if not user:
        return {'status': 'error','success': False, 'message': 'Client not found'}
    message_dict = update_request.__dict__
    if "instagram_user_id" in user:
        message_dict["instagram_user_id"] = user["instagram_user_id"]

    message_json = json.dumps( message_dict).encode('utf-8')
    producer = kafka_service.kafka_producer()
    producer.send(TOPIC_FETCH_FROM_INSTAGRAM, message_json)
    producer.flush()
    data = {key: user[key] for key in user if key != "_id"}
    response = {'status': 'success', 'success': True, 'message': 'The sync process has started'}
    response.update(data)
    return response


@app.get('/fetch-all-posts')
async def fetch_all_posts_from_all_accounts():
    # http://localhost:81/fetch-all-posts
    # fetch all posts from all client accounts
    collection = db['clients']
    clients = collection.find({"disconnect_at": None})
    for client in clients:
        sync_shop(client["instagram_username"])
    return {'status': 'success', 'message': 'All posts fetched successfully'}


@app.get("/proxy")
async def get_image(
    url: str = Query(..., description="URL of the image to fetch", example="https%3A//scontent.cdninstagram.com/v/t51.2885-19/358763655_137701106016278_1548070312046039900_n.jpg%3Fstp%3Ddst-jpg_s150x150%26_nc_ht%3Dscontent.cdninstagram.com%26_nc_cat%3D102%26_nc_ohc%3D13tV_wm2HJwAb7NwxQ1%26edm%3DAPs17CUBAAAA%26ccb%3D7-5%26oh%3D00_AfDRRQLYHbeo2Ct8Kdt44FS2Eo3dqC7W_cXQ8n9J-5Dk7w%26oe%3D6625D76D%26_nc_sid%3D10d13b")
):
    """
    Fetches an image from the given URL.

    Args:
        image_url (str): URL of the image to fetch.

    Returns:
        bytes: The image data.

    Raises:
        HTTPException: If there is an error fetching the image.
    """
    try:
        return ProxyService.fetch_image(url)
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=str(e))