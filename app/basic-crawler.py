import pickle
import datetime
import pydantic_core
from instagrapi import Client
from pymongo import MongoClient
ACCOUNT_USERNAME = ''
ACCOUNT_PASSWORD = ''
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


# user_id = cl.user_id_from_username('moshavere.by.me')
user_id = "60208601059"
print("User ID:", user_id)
medias = cl.user_medias(user_id, 200)

# store medias in mongodb

client = MongoClient('127.0.0.1', 27017)
db = client['instagram']
collection = db['posts']
for media in medias:
    json_data = media.dict()
    json_data["instagram_id"] = json_data["id"]
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
        collection.update_one({"instagram_id": json_data["instagram_id"]}, {"$set": json_data})
        
    print("Media inserted to mongodb")
    
