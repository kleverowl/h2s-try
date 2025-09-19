import json
import os
from typing import Any

from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import ToolContext
from .models import ItineraryState
from . import constants

# Construct the path to the eval directory relative to this file.
_CURRENT_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_CURRENT_FILE_DIR, ".."))
SAMPLE_SCENARIO_PATH = os.path.join(_PROJECT_ROOT, "eval", "event_plan_default.json")

def _load_precreated_plan(callback_context: CallbackContext):
    """
    Sets up the initial state.
    This gets called before the system instruction is constructed.

    Args:
        callback_context: The callback context.
    """
    if "itinerary_state" in callback_context.state:
        return

    data = {}
    try:
        with open(SAMPLE_SCENARIO_PATH, "r") as file:
            data = json.load(file)
            print(f"\nLoading Initial State from {SAMPLE_SCENARIO_PATH}\n")
    except FileNotFoundError:
        print(f"Error: {SAMPLE_SCENARIO_PATH} not found. Creating an empty initial state.")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {SAMPLE_SCENARIO_PATH}. Creating an empty initial state.")
    
    # Ensure the loaded data matches the ItineraryState structure
    if "state" in data and isinstance(data["state"], dict):
        initial_state = ItineraryState(**data["state"])
    else:
        initial_state = ItineraryState() # Return a default empty state if loading fails or format is incorrect

    callback_context.state["itinerary_state"] = initial_state.dict()
    callback_context.state[constants.STATE_INITIALIZED] = True
    callback_context.state[constants.USER_EXIST] = False

def get_state(tool_context: ToolContext) -> ItineraryState:
    """
    Gets the current itinerary state from the tool context.
    Assumes _load_precreated_plan has already initialized the state.
    """
    state_dict = tool_context.state.get("itinerary_state", {})
    return ItineraryState(**state_dict)

def update_state(tool_context: ToolContext, state: ItineraryState):
    """
    Updates the itinerary state in the tool context.
    """
    tool_context.state["itinerary_state"] = state.dict()

def update_state_field(tool_context: ToolContext, key: str, value: Any) -> str:
    """
    Updates a single field in the itinerary state.
    """
    state = get_state(tool_context)
    keys = key.split('.')
    obj = state
    for k in keys[:-1]:
        if isinstance(obj, list):
            obj = obj[int(k)]
        else:
            obj = getattr(obj, k)
    setattr(obj, keys[-1], value)
    update_state(tool_context, state)
    return "Itinerary state updated successfully."