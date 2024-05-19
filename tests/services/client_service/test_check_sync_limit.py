from freezegun import freeze_time
import mongomock
from pymongo import MongoClient
from datetime import datetime
from unittest.mock import patch
import unittest
import sys
sys.path.append('./')
import app.services.client_service as client_service

class TestCheckSyncLimit(unittest.TestCase):
    @patch('pymongo.MongoClient', new=mongomock.MongoClient)
    @freeze_time("2024-01-02 12:00:00")
    @patch('logging.error')
    def test_check_sync_limit_function_daily_successfully(self, mock_logger):
        client = MongoClient()
        db = client['test_db']

        # Initial data
        default_shop_value = {
            "instagram_username": "test_shop",
            "instagram_sync_count": 0,
            "instagram_sync_max": 30,
            "daily_instagram_sync_count": 0,
            "daily_instagram_sync_max": 5,
            "website_update_count": 0,
            "website_update_max": 50,
            "daily_website_update_count": 0,
            "daily_website_update_max": 10,
            "last_sync_at": datetime.strptime("2024-01-01 23:00:00", "%Y-%m-%d %H:%M:%S"),
            "last_website_update": datetime.strptime("2024-01-01 23:00:00", "%Y-%m-%d %H:%M:%S"),
        }

        # copy of default
        shop = default_shop_value.copy()
        shop['daily_instagram_sync_count'] = 3
        # Inserting data
        db['clients'].update_one({"instagram_username": "test_shop"}, {
                                 "$set": shop}, upsert=True)

        # Testing check_sync_limit
        result = client_service.check_sync_limit("test_shop", db)
        shop = db['clients'].find_one({"instagram_username": "test_shop"})
        self.assertEqual(result['status'], 'success')

        db["clients"].find_one_and_delete({"instagram_username": "test_shop"})

    @patch('pymongo.MongoClient', new=mongomock.MongoClient)
    @freeze_time("2024-01-02 12:00:00")
    @patch('logging.error')
    def test_check_sync_limit_function_successfully(self, mock_logger):
        client = MongoClient()
        db = client['test_db']

        # Initial data
        default_shop_value = {
            "instagram_username": "test_shop",
            "instagram_sync_count": 0,
            "instagram_sync_max": 30,
            "daily_instagram_sync_count": 0,
            "daily_instagram_sync_max": 5,
            "website_update_count": 0,
            "website_update_max": 50,
            "daily_website_update_count": 0,
            "daily_website_update_max": 10,
            "last_sync_at": datetime.strptime("2024-01-01 23:00:00", "%Y-%m-%d %H:%M:%S"),
            "last_website_update": datetime.strptime("2024-01-01 23:00:00", "%Y-%m-%d %H:%M:%S"),
        }

        # copy of default
        shop = default_shop_value.copy()
        shop['instagram_sync_count'] = 20
        # Inserting data
        db['clients'].update_one({"instagram_username": "test_shop"}, {
                                 "$set": shop}, upsert=True)

        # Testing check_sync_limit
        result = client_service.check_sync_limit("test_shop", db)
        shop = db['clients'].find_one({"instagram_username": "test_shop"})
        self.assertEqual(result['status'], 'success')

        db["clients"].find_one_and_delete({"instagram_username": "test_shop"})

    @patch('pymongo.MongoClient', new=mongomock.MongoClient)
    @freeze_time("2024-01-02 23:00:00")
    @patch('logging.error')
    def test_check_sync_limit_function_daily_failed(self, mock_logger):
        client = MongoClient()
        db = client['test_db']

        # Initial data
        default_shop_value = {
            "instagram_username": "test_shop",
            "instagram_sync_count": 0,
            "instagram_sync_max": 30,
            "daily_instagram_sync_count": 0,
            "daily_instagram_sync_max": 5,
            "website_update_count": 0,
            "website_update_max": 50,
            "daily_website_update_count": 0,
            "daily_website_update_max": 10,
            "last_sync_at": datetime.strptime("2024-01-02 12:00:00", "%Y-%m-%d %H:%M:%S"),
            "last_website_update": datetime.strptime("2024-01-02 12:00:00", "%Y-%m-%d %H:%M:%S"),
        }

        # copy of default
        shop = default_shop_value.copy()
        shop['daily_instagram_sync_count'] = 5
        # Inserting data
        db['clients'].update_one({"instagram_username": "test_shop"}, {
                                 "$set": shop}, upsert=True)

        # Testing check_sync_limit
        result = client_service.check_sync_limit("test_shop", db)
        shop = db['clients'].find_one({"instagram_username": "test_shop"})
        self.assertEqual(result['status'], 'error')

        db["clients"].find_one_and_delete({"instagram_username": "test_shop"})

    @patch('pymongo.MongoClient', new=mongomock.MongoClient)
    @freeze_time("2024-01-02 23:00:00")
    @patch('logging.error')
    def test_check_sync_limit_function_failed(self, mock_logging):
        client = MongoClient()
        db = client['test_db']

        # Initial data
        default_shop_value = {
            "instagram_username": "test_shop",
            "instagram_sync_count": 0,
            "instagram_sync_max": 30,
            "daily_instagram_sync_count": 0,
            "daily_instagram_sync_max": 5,
            "website_update_count": 0,
            "website_update_max": 50,
            "daily_website_update_count": 0,
            "daily_website_update_max": 10,
            "last_sync_at": datetime.strptime("2024-01-02 12:00:00", "%Y-%m-%d %H:%M:%S"),
            "last_website_update": datetime.strptime("2024-01-02 12:00:00", "%Y-%m-%d %H:%M:%S"),
        }

        # copy of default
        shop = default_shop_value.copy()
        shop['instagram_sync_count'] = 50
        # Inserting data
        db['clients'].update_one({"instagram_username": "test_shop"}, {
                                 "$set": shop}, upsert=True)

        # Testing check_sync_limit
        result = client_service.check_sync_limit("test_shop", db)
        shop = db['clients'].find_one({"instagram_username": "test_shop"})
        self.assertEqual(result['status'], 'error')

        db["clients"].find_one_and_delete({"instagram_username": "test_shop"})

    @patch('pymongo.MongoClient', new=mongomock.MongoClient)
    @freeze_time("2024-01-02 23:00:00")
    @patch('logging.info')
    def test_check_sync_limit_function_less_1_hour_failed(self, mock_logging):
        client = MongoClient()
        db = client['test_db']

        # Initial data
        default_shop_value = {
            "instagram_username": "test_shop",
            "instagram_sync_count": 0,
            "instagram_sync_max": 30,
            "daily_instagram_sync_count": 0,
            "daily_instagram_sync_max": 5,
            "website_update_count": 0,
            "website_update_max": 50,
            "daily_website_update_count": 0,
            "daily_website_update_max": 10,
            "last_sync_at": datetime.strptime("2024-01-02 12:00:00", "%Y-%m-%d %H:%M:%S"),
            "last_website_update": datetime.strptime("2024-01-02 12:00:00", "%Y-%m-%d %H:%M:%S"),
        }

        # copy of default
        shop = default_shop_value.copy()
        shop['last_sync_at'] = datetime.strptime("2024-01-02 22:10:00", "%Y-%m-%d %H:%M:%S")
        # Inserting data
        db['clients'].update_one({"instagram_username": "test_shop"}, {
                                 "$set": shop}, upsert=True)

        # Testing check_sync_limit
        result = client_service.check_sync_limit("test_shop", db)
        shop = db['clients'].find_one({"instagram_username": "test_shop"})
        self.assertEqual(result['status'], 'error')

        db["clients"].find_one_and_delete({"instagram_username": "test_shop"})


if __name__ == '__main__':
    unittest.main()
