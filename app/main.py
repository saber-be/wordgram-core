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
    posts = posts_collection.find({"user.username": instagram_username})
    # loop through the posts and update the client's website
    print("Updating client website1")
    products = []
    for post in posts:
        print("Updating client website")       
        #  send request to the client's website
        # url = client["product_webhook_url"]
        url = "http://92.246.138.182:8081/wp-admin/admin-ajax.php?action=wordgram-product-hook"
        json_data = instaToWordGramMapper(post)
        products.append(json_data)
        re = requests.post(url, json={"action": "addProduct", "products": [json_data]})
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
    tags = []
    lines = caption.split("\n")
    clean_caption = caption
    for line in lines:
        if "#" in line:
            line = line.replace(",", " ")
            line = line.replace("#", " #")
            line_tags = line.split(" ")
            line_tags = [tag[1:] for tag in line_tags if tag.startswith("#")]
            tags = tags + line_tags
    # remove tags from clean_caption
    for tag in tags:
        clean_caption = clean_caption.replace(f"#{tag}", "")
    return tags, clean_caption

def getPostTags(tags):
    # example : ["tag1", "tag2"]
    # output : [{"name": "tag1"}, {"name": "tag2"}]
    postTags = []
    for tag in tags:
        postTags.append({"name": tag})
    return postTags