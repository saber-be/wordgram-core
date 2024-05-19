import sys
sys.path.append('./')
import app.services.client_service as client_service
import unittest
from unittest.mock import patch
from datetime import datetime
from pymongo import MongoClient
import mongomock
from freezegun import freeze_time

class TestSyncCounterIncrement(unittest.TestCase):
    @patch('pymongo.MongoClient', new=mongomock.MongoClient)
    @freeze_time("2024-01-02 12:00:00")
    def test_sync_counter_increment_function_successfully(self):
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
        # Inserting data
        db['clients'].update_one({"instagram_username": "test_shop"}, {"$set": shop}, upsert=True)

        # Testing sync_counter_increment
        client_service.sync_counter_increment("test_shop", db)
        shop = db['clients'].find_one({"instagram_username": "test_shop"})
        self.assertEqual(shop['daily_instagram_sync_count'], 1)
        self.assertEqual(shop['instagram_sync_count'], 1)
        self.assertEqual(shop['last_sync_at'], datetime.now())

        db["clients"].find_one_and_delete({"instagram_username": "test_shop"})

    @patch('pymongo.MongoClient', new=mongomock.MongoClient)
    @freeze_time("2024-01-02 23:00:00")
    def test_sync_counter_increment_function_unset_keys(self):
        client = MongoClient()
        db = client['test_db']

        # Initial data
        default_shop_value = {
            "instagram_username": "test_shop"
        }

        # copy of default
        shop = default_shop_value.copy()
        # Inserting data
        db['clients'].update_one({"instagram_username": "test_shop"}, {"$set": shop}, upsert=True)

        # Testing sync_counter_increment
        client_service.sync_counter_increment("test_shop", db)
        shop = db['clients'].find_one({"instagram_username": "test_shop"})
        self.assertEqual(shop['daily_instagram_sync_count'], 1)
        self.assertEqual(shop['instagram_sync_count'], 1)
        self.assertEqual(shop['last_sync_at'], datetime.now())

        db["clients"].find_one_and_delete({"instagram_username": "test_shop"})


if __name__ == '__main__':
    unittest.main()
