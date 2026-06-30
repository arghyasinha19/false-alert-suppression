import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Ensure root dir in path to import MongoDBClient
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from workflow.tools.mongodb_client import MongoDBClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DashboardAPI")

app = FastAPI(title="False Alert Suppression API")

# Allow Vite React app to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mongo = MongoDBClient()

@app.get("/api/alerts")
def get_alerts():
    """Fetch all processed alerts from MongoDB."""
    collection = mongo.get_collection("alert_results")
    if collection is None:
        return {"error": "MongoDB not connected", "alerts": []}
        
    try:
        # Fetch all, omitting the internal MongoDB _id
        alerts = list(collection.find({}, {"_id": 0}))
        
        # Extract unique incident numbers
        incident_numbers = set()
        for a in alerts:
            inc = a.get("results", {}).get("agent_4", {}).get("data", {}).get("incident")
            if inc and inc != "Unknown":
                incident_numbers.add(inc)
                
        # Bulk fetch live statuses from ServiceNow
        snow_statuses = {}
        if incident_numbers:
            from workflow.tools.servicenow_client import ServiceNowClient
            snow_client = ServiceNowClient()
            snow_statuses = snow_client.get_incidents_by_numbers(list(incident_numbers))
            
        # Enrich the alerts with the live status
        for a in alerts:
            inc = a.get("results", {}).get("agent_4", {}).get("data", {}).get("incident")
            if inc in snow_statuses:
                a["live_snow_status"] = snow_statuses[inc]
                
        return {"alerts": alerts}
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        return {"error": str(e), "alerts": []}
