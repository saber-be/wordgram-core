from fastapi import FastAPI
from pymongo import MongoClient
import datetime
from pymongo.errors import ServerSelectionTimeoutError

app = FastAPI()

client = MongoClient('mongo', 27017)
db = client['instagram']
collection = db['clients']


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
