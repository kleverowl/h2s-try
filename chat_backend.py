import os
import sys
from datetime import datetime, timezone
import logging
import json
from typing import Optional

import firebase_admin
from firebase_admin import credentials, db
from fastapi import FastAPI, HTTPException, Body, BackgroundTasks
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import uvicorn

from main_agent.remote_connections import RemoteConnections

# Load environment variables from .env file
load_dotenv()

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Firebase Initialization ---
try:
    logger.info("Attempting to initialize Firebase...")
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    firebase_database_url = os.getenv("FIREBASE_DATABASE_URL")

    if not cred_path:
        logger.critical("FATAL: GOOGLE_APPLICATION_CREDENTIALS environment variable is not set.")
        sys.exit("Exiting: GOOGLE_APPLICATION_CREDENTIALS is not set.")

    if not os.path.exists(cred_path):
        logger.critical(f"FATAL: Service account key file not found at path: {cred_path}")
        sys.exit(f"Exiting: Service account key file not found at path: {cred_path}")

    if not firebase_database_url:
        logger.critical("FATAL: FIREBASE_DATABASE_URL environment variable is not set.")
        sys.exit("Exiting: FIREBASE_DATABASE_URL is not set.")

    if not firebase_admin._apps:  # 👈 check if already initialized
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': firebase_database_url
        })
        logger.info("Firebase initialized successfully.")
    else:
        logger.info("Firebase already initialized. Skipping re-initialization.")

except Exception as e:
    logger.critical(f"CRITICAL: Firebase initialization error: {e}", exc_info=True)
    sys.exit(1)
app = FastAPI()

# --- Pydantic Models ---
class ChatRequest(BaseModel):
    user_id: str = Field(..., example="user123")
    itinerary_id: str = Field(..., example="itinerary456")
    message: str = Field(..., example="Hello, I need help with my trip.")

class Message(BaseModel):
    sender: str
    message: str
    timestamp: str
    message_type: str = "text"
    activityType: Optional[str] = None
    activity_object: Optional[str] = None
    bookingRef: Optional[str] = None

# --- AI Agent Communication ---
async def get_agent_response(user_message: str) -> str:
    logger.info(f"Getting agent response for: '{user_message}'")
    main_agent_url = os.getenv("HOST_AGENT_A2A_URL")
    if not main_agent_url:
        logger.error("MAIN_AGENT_URL environment variable not set.")
        return "Error: Main agent URL not configured."

    try:
        connections = await RemoteConnections.create()
        response_dict = await connections.invoke_agent(main_agent_url, user_message)
        await connections.close()

        if "result" in response_dict:
            try:
                # The result from the agent is a JSON string, so we parse it.
                agent_output = json.loads(response_dict["result"])
                message = agent_output.get("result", "")
                state = agent_output.get("state", {})

                # Log the state
                logger.info(f"Received state from agent: {state}")

                return message
            except (json.JSONDecodeError, TypeError):
                # Fallback for when the response is not a valid JSON string
                logger.warning("Could not decode JSON from agent response, returning as is.")
                return response_dict["result"]
        else:
            error_message = response_dict.get("error", "Unknown error from agent.")
            logger.error(f"Error from main agent: {error_message}")
            return f"Error: {error_message}"
    except Exception as e:
        logger.error(f"Failed to connect to main agent: {e}", exc_info=True)
        return "Error: Could not connect to the main agent."

# --- Background Task ---
async def process_agent_response_in_background(user_id: str, itinerary_id: str, user_message_text: str):
    messages_path = f"users/user_id/{user_id}/itineraries/{itinerary_id}/messages/message_id"
    messages_ref = db.reference(messages_path)
    typing_ref = db.reference(f"users/user_id/{user_id}/itineraries/{itinerary_id}/messages")

    logger.info(f"Background task: Processing agent response for user: {user_id}")
    try:
        agent_response_text = await get_agent_response(user_message_text)

        agent_message = Message(
            sender="model",
            message=agent_response_text,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        messages_ref.push(agent_message.model_dump())
        logger.info("Background task: Agent message stored successfully.")

    except Exception as e:
        logger.error(f"Error in background agent processing: {e}", exc_info=True)
        try:
            error_message = Message(
                sender="model",
                message=f"Sorry, an error occurred: {str(e)}",
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            messages_ref.push(error_message.model_dump())
        except Exception as db_e:
            logger.error(f"Could not save error message to Firebase: {db_e}", exc_info=True)
    finally:
        try:
            typing_ref.update({"typing": False})
        except Exception as db_e:
            logger.error(f"Could not set typing to false: {db_e}", exc_info=True)

# --- API Endpoint ---
@app.post("/chat")
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    logger.info(f"Received chat request from user: {request.user_id}")
    typing_ref = db.reference(f"users/user_id/{request.user_id}/itineraries/{request.itinerary_id}/messages")

    try:
        typing_ref.update({"typing": True})
    except Exception as e:
        logger.error(f"Error setting typing indicator: {e}", exc_info=True)

    # Add background task (runs after sending API response)
    background_tasks.add_task(
        process_agent_response_in_background,
        request.user_id,
        request.itinerary_id,
        request.message
    )

    # Return immediately, no delays
    return {
        "status": "success",
        "message": "Message received and being processed"
    }

# --- Uvicorn Entrypoint ---
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8014))
    logger.info(f"Starting FastAPI server on http://127.0.0.1:{port}")
    uvicorn.run("chat_backend:app", host="127.0.0.1", port=port, reload=False)
