"""Configuration settings for the ADK A2A integration."""

import os
from typing import Final
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
GOOGLE_API_KEY: Final[str] = os.getenv("GOOGLE_API_KEY", "")


# A2A Service URLs
WEATHER_AGENT_A2A_URL: Final[str] = os.getenv("WEATHER_AGENT_A2A_URL", "http://localhost:8004")
FLIGHT_AGENT_A2A_URL: Final[str] = os.getenv("FLIGHT_AGENT_A2A_URL", "http://localhost:8002")
FOOD_AGENT_A2A_URL: Final[str] = os.getenv("FOOD_AGENT_A2A_URL", "http://localhost:8003")
ACTIVITY_AGENT_A2A_URL: Final[str] = os.getenv("ACTIVITY_AGENT_A2A_URL", "http://localhost:8005")
BUDGET_AGENT_A2A_URL: Final[str] = os.getenv("BUDGET_AGENT_A2A_URL", "http://localhost:8006")
CAB_AGENT_A2A_URL: Final[str] = os.getenv("CAB_AGENT_A2A_URL", "http://localhost:8007")
CURRENCY_AGENT_A2A_URL: Final[str] = os.getenv("CURRENCY_AGENT_A2A_URL", "http://localhost:8008")
DOCUMENT_AGENT_A2A_URL: Final[str] = os.getenv("DOCUMENT_AGENT_A2A_URL", "http://localhost:8009")
HOTEL_AGENT_A2A_URL: Final[str] = os.getenv("HOTEL_AGENT_A2A_URL", "http://localhost:8010")
HOST_AGENT_A2A_URL: Final[str] = os.getenv("HOST_AGENT_A2A_URL", "http://localhost:8000")

# ADK Configuration
ADK_MODEL: Final[str] = os.getenv("ADK_MODEL", "gemini-2.0-flash")