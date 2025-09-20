import os
import sys
import uuid
from datetime import datetime, timezone
import time
import logging

import firebase_admin
from firebase_admin import credentials, db
from fastapi import BackgroundTasks, FastAPI, HTTPException, Body
from pydantic import BaseModel, Field
from dotenv import load_dotenv

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

    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {
        'databaseURL': firebase_database_url
    })
    logger.info("Firebase initialized successfully.")

except (ValueError, SystemExit) as e:
    logger.error(e)
    sys.exit(1)
except Exception as e:
    logger.critical(f"CRITICAL: An unexpected error occurred during Firebase initialization: {e}", exc_info=True)
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
    activityType: str = None
    activity_object: str = None
    bookingRef: str = None
    message_type: str = "text"

# --- AI Agent Communication ---

async def process_agent_response(
    user_message_text: str, user_id: str, itinerary_id: str
):
    """
    Background task to get agent response and update Firebase.
    """
    messages_path = f"users/{user_id}/itineraries/{itinerary_id}/messages"
    messages_ref = db.reference(messages_path)

    try:
        agent_response_text = await get_agent_response(user_message_text)

        if "Error:" not in agent_response_text:
            agent_message = Message(
                sender="model",
                message=agent_response_text,
                timestamp=datetime.now(timezone.utc).isoformat(),
                activityType=None,
                activity_object=None,
                bookingRef=None,
                message_type="text",
            )
            # Use a new UUID for the agent's message
            agent_message_id = str(uuid.uuid4())
            messages_ref.child(agent_message_id).set(agent_message.model_dump())
            logger.info("Agent message stored successfully.")

    except Exception as e:
        logger.error(
            f"An error occurred during agent processing in background: {e}",
            exc_info=True,
        )
    finally:
        # Always set typing to false, even if there was an error.
        logger.info("Setting typing indicator to False.")
        messages_ref.update({"typing": False})

async def get_agent_response(user_message: str) -> str:
    """
    Calls the main agent to get a response.
    """
    logger.info(f"Getting agent response for: '{user_message}'")
    main_agent_url = os.getenv("MAIN_AGENT_URL")
    if not main_agent_url:
        logger.error("MAIN_AGENT_URL environment variable not set.")
        return "Error: Main agent URL not configured."

    try:
        connections = await RemoteConnections.create()
        response_dict = await connections.invoke_agent(main_agent_url, user_message)
        await connections.close()

        if "result" in response_dict:
            return response_dict["result"]
        else:
            error_message = response_dict.get("error", "Unknown error from agent.")
            logger.error(f"Error from main agent: {error_message}")
            return f"Error: {error_message}"
    except Exception as e:
        logger.error(f"Failed to connect to main agent: {e}", exc_info=True)
        return "Error: Could not connect to the main agent."

# --- API Endpoint ---

@app.post("/chat")
async def chat(
    request: ChatRequest = Body(...), background_tasks: BackgroundTasks = None
):
    """
    Handles incoming chat messages. Stores the user's message in Firebase,
    triggers a background task to get the agent's response, and returns
    an immediate success response.
    """
    logger.info(f"Received chat request: {request.model_dump()}")

    user_id = request.user_id
    itinerary_id = request.itinerary_id
    user_message_text = request.message

    messages_path = f"users/{user_id}/itineraries/{itinerary_id}/messages"
    messages_ref = db.reference(messages_path)

    try:
        # 1. Store user message in Firebase with a unique ID
        user_message_id = str(uuid.uuid4())
        user_message = Message(
            sender="user",
            message=user_message_text,
            timestamp=datetime.now(timezone.utc).isoformat(),
            activityType=None,
            activity_object=None,
            bookingRef=None,
            message_type="text",
        )
        messages_ref.child(user_message_id).set(user_message.model_dump())
        logger.info("User message stored successfully.")

        # 2. Set typing: true
        logger.info("Setting typing indicator to True.")
        messages_ref.update({"typing": True})

        # 3. Add agent processing to background tasks
        background_tasks.add_task(
            process_agent_response, user_message_text, user_id, itinerary_id
        )
        logger.info("Agent processing added to background tasks.")

        # 4. Return immediate success response
        logger.info("Chat request processed successfully, returning immediate response.")
        return {"status": "success", "message": "Message sent to agent"}

    except Exception as e:
        logger.error(f"An error occurred during chat processing: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"An internal error occurred: {e}"
        )

# --- Helper for running with uvicorn ---
if __name__ == "__main__":
    import uvicorn
    # Port can be configured via an environment variable or defaults to 8000
    port = int(os.getenv("PORT", 8014))
    logger.info("Starting FastAPI server with uvicorn.")
    logger.info(f"Access the interactive API docs at http://127.0.0.1:{port}/docs")
    uvicorn.run(app, host="127.0.0.1", port=port)