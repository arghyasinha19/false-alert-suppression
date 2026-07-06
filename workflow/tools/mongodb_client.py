import os
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

from dotenv import load_dotenv

logger = logging.getLogger(__name__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(project_root, ".env")
load_dotenv(dotenv_path=env_path)

class MongoDBClient:
    def __init__(self):
        self.uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.db_name = os.getenv("MONGO_DB_NAME", "false_alert_suppression")
        self.client = None
        self.db = None
        self._connect()
        
    def _connect(self):
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            # Verify the connection
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            logger.info(f"Successfully connected to MongoDB database: {self.db_name}")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB at {self.uri}: {e}")
            
    def get_collection(self, collection_name: str):
        if self.db is not None:
            return self.db[collection_name]
        return None
        
    def save_alert_result(self, alert_id: str, payload: dict):
        """Save or update the final execution state of an alert."""
        collection = self.get_collection("alert_results")
        if collection is not None:
            try:
                # Upsert based on alert_id to track lifecycle updates
                collection.update_one(
                    {"alert_id": alert_id},
                    {"$set": payload},
                    upsert=True
                )
                logger.info(f"Saved alert {alert_id} to MongoDB.")
                return True
            except Exception as e:
                logger.error(f"Failed to save alert {alert_id} to MongoDB: {e}")
                return False
        return False
