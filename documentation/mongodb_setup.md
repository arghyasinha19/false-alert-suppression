# MongoDB Setup Guide

The False Alert Suppression system uses MongoDB as its primary persistence layer to store the final execution traces of the agentic workflow (via the Reporter node) and serve them to the React Dashboard.

Here are the step-by-step instructions to set up MongoDB for this project.

## Option 1: Using Docker (Recommended for Local Development)

The fastest and cleanest way to run MongoDB locally is using Docker.

1. Ensure [Docker Desktop](https://www.docker.com/products/docker-desktop) is installed and running.
2. Open your terminal or PowerShell.
3. Run the following command to pull and start the MongoDB container in the background:
   ```bash
   docker run -d -p 27017:27017 --name mongo-false-alert mongo:latest
   ```
4. Verify the container is running:
   ```bash
   docker ps
   ```

*To stop the database later, run `docker stop mongo-false-alert`. To start it again, run `docker start mongo-false-alert`.*

## Option 2: Native Windows Installation

If you prefer to install MongoDB directly onto your Windows machine as a background service:

1. Go to the [MongoDB Community Server Download Page](https://www.mongodb.com/try/download/community).
2. Select **Windows** as the Platform and **msi** as the Package, then click **Download**.
3. Run the downloaded installer.
4. Choose the **Complete** setup type.
5. On the Service Configuration screen, leave **"Install MongoD as a Service"** checked. This ensures MongoDB starts automatically with Windows.
6. (Optional) Leave "Install MongoDB Compass" checked if you want a visual GUI to inspect your database records.
7. Finish the installation.

## Project Configuration

Once MongoDB is running (either via Docker or natively), ensure your `.env` file points to it. Open the `.env` file at the root of the project and verify these lines exist:

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=false_alert_suppression
```

### Do I need to create tables or schemas?

**No.** MongoDB is a NoSQL document database. You do not need to manually create the database or any tables. 

The first time the LangGraph workflow finishes processing an alert, the `Reporter` node will connect to MongoDB and automatically create the `false_alert_suppression` database and the `alert_results` collection, inserting the data immediately.
