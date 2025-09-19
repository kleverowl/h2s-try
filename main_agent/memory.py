import json
import os
from typing import Any, Dict, List
from pydantic import BaseModel

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

def _update_nested_field(obj: Any, keys: List[str], value: Any):
    """
    Recursively traverses the object structure to update a nested field.
    """
    key = keys[0]
    if len(keys) == 1:
        if isinstance(obj, BaseModel):
            setattr(obj, key, value)
        elif isinstance(obj, dict):
            obj[key] = value
        elif isinstance(obj, list):
            obj[int(key)] = value
        return

    next_obj = None
    if isinstance(obj, BaseModel):
        next_obj = getattr(obj, key)
    elif isinstance(obj, dict):
        next_obj = obj.get(key)
    elif isinstance(obj, list):
        try:
            next_obj = obj[int(key)]
        except IndexError:
            # If the index is out of bounds, we cannot proceed.
            # This case might need specific handling based on requirements,
            # such as appending to the list if the index is equivalent to the list's length.
            return

    if next_obj is not None:
        _update_nested_field(next_obj, keys[1:], value)


def update_state_field(tool_context: ToolContext, key: str, value: Any) -> str:
    """
    Updates a single field in the itinerary state.
    """
    state = get_state(tool_context)
    keys = key.split('.')
    _update_nested_field(state, keys, value)
    update_state(tool_context, state)
    return "Itinerary state updated successfully."