import logging
import traceback
from pymongo import MongoClient
from app.models.log import Log
from typing import List
import os
import datetime

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
    
class MongoHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.log_service = LogService()

    def emit(self, record):
        log_entry = {
            "message": self.format(record),
            "level": record.levelname,
            "timestamp": record.created
        }
        self.log_service.save_log(log_entry)

class FileHandler(logging.Handler):
    def __init__(self, dir_path: str):
        super().__init__()
        self.dir_path = dir_path

    def emit(self, record):
        file_path = os.path.join(self.dir_path, datetime.datetime.now().strftime("%Y-%m-%d") + ".log")
        with open(file_path, 'a') as file:
            log_message = self.format(record)
            file.write(log_message + "\n")