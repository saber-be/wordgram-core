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
from app.services.kafka_service import KafkaService, TOPIC_FETCH_FROM_INSTAGRAM
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
WP_UPDATER_TOPIC = os.getenv('WP_UPDATER_TOPIC')




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

@app.post('/fetch-from-instagram', response_model=dict)
async def sync_shop(certificate: Certificate):
    collection = db['clients']
    query_find = {
        "instagram_username": certificate.instagram_username, "state": certificate.state, "api_key": certificate.api_key}
    user = collection.find_one(query_find)
    if not user:
        return {'status': 'error','success': False, 'message': 'Client not found'}
    message_dict = {
        "instagram_username": certificate.instagram_username
    }
    message_json = json.dumps(message_dict).encode('utf-8')
    kafka_service.kafka_producer().send(TOPIC_FETCH_FROM_INSTAGRAM, message_json)
    data = {key: user[key] for key in user if key != "_id"}
    response = {'status': 'success', 'success': True, 'message': 'The sync process has started'}
    response.update(data)
    return response

@app.post('/update-client-website')
async def update_client_website(update_request: updateWebSiteRequest):
    message_json = json.dumps(update_request.model_dump()).encode('utf-8')
    kafka_service.kafka_producer().send(WP_UPDATER_TOPIC, message_json)
    return {'status': 'success', 'message': 'Update request sent successfully'}
    



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
    image_url: str = Query(..., description="URL of the image to fetch", example="https%3A//scontent.cdninstagram.com/v/t51.2885-19/358763655_137701106016278_1548070312046039900_n.jpg%3Fstp%3Ddst-jpg_s150x150%26_nc_ht%3Dscontent.cdninstagram.com%26_nc_cat%3D102%26_nc_ohc%3D13tV_wm2HJwAb7NwxQ1%26edm%3DAPs17CUBAAAA%26ccb%3D7-5%26oh%3D00_AfDRRQLYHbeo2Ct8Kdt44FS2Eo3dqC7W_cXQ8n9J-5Dk7w%26oe%3D6625D76D%26_nc_sid%3D10d13b")
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
        return ProxyService.fetch_image(image_url)
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=str(e))