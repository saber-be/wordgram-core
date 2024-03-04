import requests
from fastapi import FastAPI
from pymongo import MongoClient
import datetime
from pymongo.errors import ServerSelectionTimeoutError
import pickle
import datetime
import pydantic_core
from instagrapi import Client
from pymongo import MongoClient
import os

app = FastAPI()

client = MongoClient('mongo', 27017)
db = client['instagram']



@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get('/register-shop')
def register_shop(shop_name: str, platform: str, platform_url: str, redirect_url: str, product_webhook_url: str, order_webhook_url: str, instagram_username: str):
    # http://localhost:81/register-shop?shop_name=WordGram&platform=WordPress/WooCommerce&platform_url=http://localhost:8080&redirect_url=http://localhost:8080/wp-admin/admin-post.php?action=wordgram-connect-response&state=4186665e47da5dd33b&product_webhook_url=http://localhost:8080/wp-admin/admin-ajax.php?action=wordgram-product-hook&order_webhook_url=http://localhost:8080/wp-admin/admin-ajax.php?action=wordgram-order-hook&instagram_username=mosakbary
    data = {
        'shop_name': shop_name,
        'platform': platform,
        'platform_url': platform_url,
        'redirect_url': redirect_url,
        'product_webhook_url': product_webhook_url,
        'order_webhook_url': order_webhook_url,
        'instagram_username': instagram_username,
        'created_at': datetime.datetime.now()
    }
    # insert to mongodb
    collection = db['clients']
    try:
        if collection.find_one({"instagram_username": data["instagram_username"]}) is None:
            print("Inserting to mongodb")
            collection.insert_one(data)
        else:
            print("Updating to mongodb")
            # update the document
            collection.update_one(
                {"instagram_username": data["instagram_username"]}, {"$set": data})
        return {'status': 'success', 'message': 'Shop registered successfully'}
    except ServerSelectionTimeoutError:
        return {'status': 'error', 'message': 'Failed to connect to the MongoDB server'}

@app.get('/fetch-from-instagram')
def sync_shop(instagram_username: str):
    # http://localhost:81/sync-shop?instagram_username=mosakbary
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
        json_data["created_at"] = datetime.datetime.now()
        # insert to mongodb
        if collection.find_one({"instagram_id": json_data["instagram_id"]}) is None:
            print("Inserting to mongodb")
            try:
                collection.insert_one(json_data)
            except:
                print("Error inserting to mongodb")
        else:
            print("Updating to mongodb")
            # update the document
            collection.update_one(
                {"instagram_id": json_data["instagram_id"]}, {"$set": json_data})
    return {'status': 'success', 'message': 'Shop synced successfully'}

@app.get('/update-client-website')
def update_client_website(instagram_username: str):
    # http://localhost:81/update-client-website?instagram_username=mosakbary
    # get posts from mongodb and update the client's website
    posts_collection = db['posts']
    client_collection = db['clients']
    # client = client_collection.find_one({"instagram_username": instagram_username})
    posts = posts_collection.find({"instagram_user_id": instagram_username})
    # loop through the posts and update the client's website
    print("Updating client website1")
    for post in posts:
        print("Updating client website")       
        #  send request to the client's website
        url = "http://192.168.100.3:8080/wp-admin/admin-ajax.php?action=wordgram-product-hook"
        json_data = instaToWordGramMapper(post)

        requests.post(url, json={"action": "addProduct", "products": [json_data]})
        
        
    return {'status': 'success', 'message': 'Client website updated successfully'}
    


def instaToWordGramMapper(instaPost):
    print(instaPost)
    wordGramPost = {
        "Name": instaPost["caption_text"][:50],
        "Description": instaPost["caption_text"],
        "Price": 9.99,
        "QTY": 10,
        "tags": [
            {
            "name": "TAG_1"
            },
            {
            "name": "TAG_2"
            }
        ],
        "Images": [
            {
            "url": instaPost["thumbnail_url"]
            }
        ]
    }
    return wordGramPost