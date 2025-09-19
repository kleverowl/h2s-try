"""Host Agent tools for A2A communication with other agents."""

import asyncio
import json
import os
import sys
from typing import Dict, Any

from config import (
    FLIGHT_AGENT_A2A_URL,
    WEATHER_AGENT_A2A_URL,
    FOOD_AGENT_A2A_URL,
    ACTIVITY_AGENT_A2A_URL,
    BUDGET_AGENT_A2A_URL,
    CAB_AGENT_A2A_URL,
    CURRENCY_AGENT_A2A_URL,
    DOCUMENT_AGENT_A2A_URL,
    HOTEL_AGENT_A2A_URL,
)
from main_agent.remote_connections import RemoteConnections
from main_agent.memory import update_state_field

# Add project root to the Python path to resolve module import errors
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mapping of agent names to their URLs.
AGENT_URL_MAP: Dict[str, str] = {
    "flight_concierge": FLIGHT_AGENT_A2A_URL,
    "weather_concierge": WEATHER_AGENT_A2A_URL,
    "food_concierge": FOOD_AGENT_A2A_URL,
    "activity_concierge": ACTIVITY_AGENT_A2A_URL,
    "budget_concierge": BUDGET_AGENT_A2A_URL,
    "cab_concierge": CAB_AGENT_A2A_URL,
    "currency_concierge": CURRENCY_AGENT_A2A_URL,
    "document_concierge": DOCUMENT_AGENT_A2A_URL,
    "hotel_concierge": HOTEL_AGENT_A2A_URL,
}


async def delegate_task(agent_name: str, task_description: str) -> Dict[str, Any]:
    """Delegates a task to a specified child agent via A2A protocol."""
    if agent_name not in AGENT_URL_MAP:
        return {"error": f"Agent '{agent_name}' is not a known agent."}

    agent_url = AGENT_URL_MAP[agent_name]
    remote_connections = await RemoteConnections.create(timeout=60.0)

    try:
        result = await remote_connections.invoke_agent(agent_url, task_description)

        if isinstance(result, dict) and result.get("error"):
            return {"error": f"Error from {agent_name}: {result['error']}"}

        # Attempt to parse the result as JSON
        try:
            return json.loads(result["result"])
        except (json.JSONDecodeError, KeyError):
            return {"result": result.get("result")}

    except Exception as e:
        return {"error": f"Error delegating task to {agent_name}: {str(e)}"}
    finally:
        await remote_connections.close()

def delegate_task_sync(agent_name: str, task_description: str) -> Dict[str, Any]:
    """Synchronous wrapper for delegate_task to be used as an ADK tool."""
    try:
        try:
            asyncio.get_running_loop()
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, delegate_task(agent_name, task_description)
                )
                return future.result(timeout=90)
        except RuntimeError:
            return asyncio.run(delegate_task(agent_name, task_description))
    except Exception as e:
        return {"error": f"Error in sync delegation wrapper: {str(e)}"}

TOOLS = {
    "update_state_field": update_state_field,
    "delegate_task_to_agent": delegate_task_sync,
}
