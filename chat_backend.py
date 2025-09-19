import os
import sys
from datetime import datetime, timezone
import time
import logging

import firebase_admin
from firebase_admin import credentials, db
from fastapi import FastAPI, HTTPException, Body
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

# --- AI Agent Communication ---

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
async def chat(request: ChatRequest = Body(...)):
    """
    Handles incoming chat messages, stores them in Firebase,
    gets a response from an AI agent, and stores that response.
    """
    logger.info(f"Received chat request: {request.model_dump()}")

    user_id = request.user_id
    itinerary_id = request.itinerary_id
    user_message_text = request.message

    messages_path = f"users/{user_id}/itineraries/{itinerary_id}/messages"
    messages_ref = db.reference(messages_path)
    
    logger.info(f"Using Firebase messages path: {messages_path}")

    try:
        # 1. Store user message in Firebase
        user_message = Message(
            sender="user",
            message=user_message_text,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        logger.info(f"Pushing user message to Firebase: {user_message.model_dump()}")
        messages_ref.push(user_message.model_dump())
        logger.info("User message stored successfully.")

        # 2. Set typing: true
        logger.info("Setting typing indicator to True.")
        messages_ref.update({"typing": True})

        # 3. Get response from AI agent
        agent_response_text = await get_agent_response(user_message_text)

        # 4. Store agent's response in Firebase
        agent_message = Message(
            sender="agent",
            message=agent_response_text,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        logger.info(f"Pushing agent message to Firebase: {agent_message.model_dump()}")
        messages_ref.push(agent_message.model_dump())
        logger.info("Agent message stored successfully.")

        # 5. Set typing: false
        logger.info("Setting typing indicator to False.")
        messages_ref.update({"typing": False})

        logger.info("Chat request processed successfully.")
        return {"status": "success", "response": agent_response_text}

    except Exception as e:
        logger.error(f"An error occurred during chat processing: {e}", exc_info=True)
        try:
            logger.warning("Attempting to set typing indicator to False after error.")
            messages_ref.update({"typing": False})
        except Exception as db_e:
            logger.error(f"Could not set typing to false after an error: {db_e}", exc_info=True)
        
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")

# --- Helper for running with uvicorn ---
if __name__ == "__main__":
    import uvicorn
    # Port can be configured via an environment variable or defaults to 8000
    port = int(os.getenv("PORT", 8014))
    logger.info("Starting FastAPI server with uvicorn.")
    logger.info(f"Access the interactive API docs at http://127.0.0.1:{port}/docs")
    uvicorn.run(app, host="127.0.0.1", port=port)