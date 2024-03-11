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
import re
from .model.Shop import Shop
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

client = MongoClient(os.environ.get('MONGO_HOST'), int(os.environ.get('MONGO_PORT')))
db = client['instagram']



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
def register_shop(shop:Shop):
    # http://localhost:81/register-shop?shop_name=WordGram&platform=WordPress/WooCommerce&platform_url=http://localhost:8080&redirect_url=http://localhost:8080/wp-admin/admin-post.php?action=wordgram-connect-response&state=4186665e47da5dd33b&product_webhook_url=http://localhost:8080/wp-admin/admin-ajax.php?action=wordgram-product-hook&order_webhook_url=http://localhost:8080/wp-admin/admin-ajax.php?action=wordgram-order-hook&instagram_username=mosakbary
    
    shop.created_at = datetime.datetime.now()
    # insert to mongodb
    collection = db['clients']
    try:
        if collection.find_one({"instagram_username": shop.instagram_username}) is None:
            print("Inserting to mongodb" ,shop.instagram_username)
            collection.insert_one(shop.__dict__)
        else:
            print("Updating to mongodb", shop.instagram_username)
            # update the document
            collection.update_one(
                {"instagram_username": shop.instagram_username}, {"$set": shop.__dict__})
        return {'status': 'success', 'message': 'Shop registered successfully', 'data': shop.__dict__}
    except ServerSelectionTimeoutError:
        return {'status': 'error', 'message': 'Failed to connect to the MongoDB server'}

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

@app.get('/update-client-website')
def update_client_website(instagram_username: str):
    # http://localhost:81/update-client-website?instagram_username=mosakbary
    # get posts from mongodb and update the client's website
    posts_collection = db['posts']
    client_collection = db['clients']
    client = client_collection.find_one({"instagram_username": instagram_username})
    posts = posts_collection.find({"user.username": instagram_username})
    # loop through the posts and update the client's website
    print("Updating client website1")
    products = []
    for post in posts:
        print("Updating client website")       
        #  send request to the client's website
        url = client["product_webhook_url"]
        # url = "http://192.168.100.9:8081/wp-admin/admin-ajax.php?action=wordgram-product-hook"
        if 'published_at' in post and 'updated_at' in post and post["published_at"] and post["published_at"] >= post["updated_at"]:
            continue
        json_data = instaToWordGramMapper(post)
        products.append(json_data)
        re = requests.post(url, json={"action": "addProduct", "products": [json_data]})
        if re.status_code == 200:
            posts_collection.update_one(
                {"instagram_id": post["instagram_id"]}, {"$set": {"published_at": datetime.datetime.now()}})
        print(re.text)
        
        
    return {'status': 'success', 'message': 'Client website updated successfully'}
    


def instaToWordGramMapper(instaPost):
    print(instaPost)
    caption = instaPost["caption_text"].split("\n")
    name = caption[0][:50]
    description = instaPost["caption_text"]
    
    if len(caption) > 1:
        description = "\n".join(caption[1:])

    tags, clean_description = getTagsAndCaption(description)
    wordGramPost = {
        "Name": name,
        "Description": clean_description,
        "SKU": instaPost["code"],
        "Price": getPrice(instaPost["caption_text"]),
        "QTY": 100,
        "tags": getPostTags(tags),
        "Images": []
    }
    thumbnail = instaPost["thumbnail_url"]
    if(thumbnail):
        wordGramPost["Images"].append({"url": thumbnail})

    images = instaPost["resources"]
    for image in images:
        wordGramPost["Images"].append({"url": image["thumbnail_url"]})

    return wordGramPost




def getPrice(caption):
    # example : قیمت💰: 448 تومان 
    # output : 448
    price = 0
    caption = caption.split("\n")
    for line in caption:
        if "قیمت" in line:
            price = line
            price = ''.join(filter(str.isdigit, price))
            if price.isdigit():
                price = int(price) * 1000
                break
    return price

def getTagsAndCaption(caption):
    # example : #tag1 #tag2
    # output : ["tag1", "tag2"]
    clean_caption = caption
    tags = []
    if "#" in caption:
        caption = caption.replace(",", " ")
        caption = caption.replace("#", " #")
        caption_tags = caption.split(" ")
        tags = [tag[1:] for tag in caption_tags if tag.startswith("#")]
    # remove tags from clean_caption
    for tag in tags:
        clean_caption = re.sub(rf"#{tag}\b", "", clean_caption)
    return tags, clean_caption

def getPostTags(tags):
    # example : ["tag1", "tag2"]
    # output : [{"name": "tag1"}, {"name": "tag2"}]
    postTags = []
    for tag in tags:
        postTags.append({"name": tag})
    return postTags

@app.get('/fetch-all-posts')
def fetch_all_posts_from_all_accounts():
    # http://localhost:81/fetch-all-posts
    # fetch all posts from all client accounts
    collection = db['clients']
    clients = collection.find()
    for client in clients:
        sync_shop(client["instagram_username"])
    return {'status': 'success', 'message': 'All posts fetched successfully'}
