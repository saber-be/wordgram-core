import traceback
from pymongo import MongoClient
from app.models.log import Log
from typing import List
import os

class LogService:
    def __init__(self):
        self.client = MongoClient(os.environ.get('MONGO_HOST'), int(os.environ.get('MONGO_PORT')))
        self.db = self.client[os.environ.get('MONGO_DB')]
        self.logs_collection = self.db.get_collection("logs")

    def save_log(self, log: Log):
        log_dict = dict(log)
        self.logs_collection.insert_one(log_dict)

    def save_error_log(self, error: Exception):
    
        error_details = error.__dict__
        error_details["traceback"] = traceback.format_exc()
        
        error_log = Log(message=str(error), level="error", error_details=error.__dict__)
        self.save_log(error_log)

    def get_logs(self) -> List[Log]:
        logs = self.logs_collection.find()
        return [Log(**log) for log in logs]