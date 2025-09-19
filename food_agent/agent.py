import json
import os
from google.adk.agents.llm_agent import Agent
from food_agent.prompt import FOOD_CONCIERGE_PROMPT

def create_food_agent():
    food_agent = Agent(
        model='gemini-2.0-flash',
        name='food_agent',
        description='A food ordering agent that helps users find and order food from restaurants.',
        instruction=FOOD_CONCIERGE_PROMPT,
    )
    return food_agent



# Required for ADK discovery
root_agent = create_food_agent()
