import logging
import os
import datetime
from pymongo import MongoClient
from app.services.log_service import MongoHandler, FileHandler

logging.basicConfig(level=logging.INFO)
mongo_handler = MongoHandler()
file_handler = FileHandler('logs')

formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
mongo_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logging.getLogger().addHandler(mongo_handler)
logging.getLogger().addHandler(file_handler)

mongoClient = MongoClient(os.environ.get(
    'MONGO_HOST'), int(os.environ.get('MONGO_PORT')))
mongoDB = mongoClient[os.environ.get('MONGO_DB')]
MAX_SYNC_LIMIT_TIME_IN_SECONDS = 3600
MAX_WEBSITE_UPDATE_LIMIT_TIME_IN_SECONDS = 3600


def check_sync_limit(instagram_username: str, db=mongoDB):
    client_collection = db['clients']
    client = client_collection.find_one(
        {"instagram_username": instagram_username, "disconnect_at": None})
    if client is None:
        logging.error("Client not found for " +
                      instagram_username+" or client is disconnected")
        return {'status': 'error', 'message': 'Client not found'}

    if 'last_sync_at' in client and client['last_sync_at'] is not None:
        last_sync = client['last_sync_at']
        if (datetime.datetime.now() - last_sync).seconds < MAX_SYNC_LIMIT_TIME_IN_SECONDS:
            logging.info("Last sync is less then 1 hour. Skipping...")
            return {'status': 'error', 'message': 'Last sync is less then 1 hour. Skipping...'}

    if 'daily_instagram_sync_count' in client and client['daily_instagram_sync_count'] is not None:
        daily_sync_count = client['daily_instagram_sync_count']
        daily_sync_max = client['daily_instagram_sync_max']
        if daily_sync_max != -1 and daily_sync_count >= daily_sync_max:
            logging.error("Daily sync limit reached for "+instagram_username)
            return {'status': 'error', 'message': 'Daily sync limit reached'}

    if 'instagram_sync_count' in client and client['instagram_sync_count'] is not None:
        sync_count = client['instagram_sync_count']
        sync_max = client['instagram_sync_max']
        if sync_max != -1 and sync_count >= sync_max:
            logging.error("Sync limit reached for "+instagram_username)
            return {'status': 'error', 'message': 'Sync limit reached'}

    return {'status': 'success', 'message': 'Sync limit not reached'}


def check_website_update_limit(instagram_username: str, db=mongoDB):
    client_collection = db['clients']
    client = client_collection.find_one(
        {"instagram_username": instagram_username, "disconnect_at": None})
    if client is None:
        logging.error("Client not found for " +
                      instagram_username+" or client is disconnected")
        return {'status': 'error', 'message': 'Client not found'}

    if 'last_website_update' in client and client['last_website_update'] is not None:
        last_update = client['last_website_update']
        if (datetime.datetime.now() - last_update).seconds < MAX_WEBSITE_UPDATE_LIMIT_TIME_IN_SECONDS:
            logging.info(
                "Last website update is less then 1 hour. Skipping...")
            return {'status': 'error', 'message': 'Last website update is less then 1 hour. Skipping...'}

    if 'daily_website_update_count' in client and client['daily_website_update_count'] is not None:
        daily_website_update_count = client['daily_website_update_count']
        daily_website_update_max = client['daily_website_update_max']
        if daily_website_update_max != -1 and daily_website_update_count >= daily_website_update_max:
            logging.error(
                "Daily website update limit reached for "+instagram_username)
            return {'status': 'error', 'message': 'Daily website update limit reached'}

    if 'website_update_count' in client and client['website_update_count'] is not None:
        website_update_count = client['website_update_count']
        website_update_max = client['website_update_max']
        if website_update_max != -1 and website_update_count >= website_update_max:
            logging.error("Website update limit reached for " +
                          instagram_username)
            return {'status': 'error', 'message': 'Website update limit reached'}

    return {'status': 'success', 'message': 'Website update limit not reached'}


def sync_counter_increment(instagram_username: str, db=mongoDB):
    client_collection = db['clients']
    client_collection.update_one({"instagram_username": instagram_username}, {
                                 "$inc": {"instagram_sync_count": 1}})
    client_collection.update_one({"instagram_username": instagram_username}, {
                                 "$inc": {"daily_instagram_sync_count": 1}})
    client_collection.update_one({"instagram_username": instagram_username}, {
                                 "$set": {"last_sync_at": datetime.datetime.now()}})
    return {'status': 'success', 'message': 'Sync counter incremented'}


def website_update_counter_increment(instagram_username: str, db=mongoDB):
    client_collection = db['clients']
    client_collection.update_one({"instagram_username": instagram_username}, {
                                 "$inc": {"website_update_count": 1}})
    client_collection.update_one({"instagram_username": instagram_username}, {
                                 "$inc": {"daily_website_update_count": 1}})
    client_collection.update_one({"instagram_username": instagram_username}, {
                                 "$set": {"last_website_update": datetime.datetime.now()}})
    return {'status': 'success', 'message': 'Website update counter incremented'}


def daily_counter_reset(instagram_username: str, db=mongoDB):
    client_collection = db['clients']
    client = client_collection.find_one(
        {"instagram_username": instagram_username, "disconnect_at": None})
    now = datetime.datetime.now()
    yesterday = (now -
                 datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    last_update = client['last_website_update'] if (
        'last_website_update' in client and client['last_website_update'] is not None) else datetime.datetime.strptime(yesterday, "%Y-%m-%d")
    last_update_date = last_update.strftime("%Y-%m-%d")
    if (yesterday >= last_update_date):
        client_collection.update_one({"instagram_username": instagram_username}, {
            "$set": {"daily_website_update_count": 0}})

    last_sync = client['last_sync_at'] if (
        'last_sync_at' in client and client['last_sync_at'] is not None) else datetime.datetime.strptime(yesterday, "%Y-%m-%d")
    last_sync_date = last_sync.strftime("%Y-%m-%d")
    if (yesterday >= last_sync_date):
        client_collection.update_one({"instagram_username": instagram_username}, {
            "$set": {"daily_instagram_sync_count": 0}})

    return {'status': 'success', 'message': 'Daily counter reset'}
