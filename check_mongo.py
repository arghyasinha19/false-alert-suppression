import os
from pymongo import MongoClient

uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
db_name = os.getenv("MONGO_DB_NAME", "false_alert_suppression")

print(f"Connecting to MongoDB URI: {uri}")
try:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("Connected successfully!")
    db = client[db_name]
    print(f"Database: {db_name}")
    print(f"Collections: {db.list_collection_names()}")
    for col_name in db.list_collection_names():
        col = db[col_name]
        print(f"  Collection '{col_name}': {col.count_documents({})} documents")
        # print first document as sample
        sample = col.find_one()
        if sample:
            print(f"    Sample key structure: {list(sample.keys())}")
except Exception as e:
    print(f"Error: {e}")
