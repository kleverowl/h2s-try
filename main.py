import os
import uvicorn
import logging
from chat_backend import app

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Port can be configured via an environment variable or defaults to 8014
    port = int(os.getenv("PORT", 8014))
    logger.info("Starting FastAPI server with uvicorn.")
    logger.info(f"Access the interactive API docs at http://127.0.0.1:{port}/docs")
    uvicorn.run(app, host="127.0.0.1", port=port)