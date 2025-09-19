import json
import os
from google.adk.agents.llm_agent import Agent
from hotel_agent.prompt import HOTEL_CONCIERGE_PROMPT

def create_hotel_agent():
    hotel_agent = Agent(
        model='gemini-2.0-flash',
        name='hotel_agent',
        description='A hotel booking agent that helps users find and book hotels based on their preferences.',
        instruction=HOTEL_CONCIERGE_PROMPT,
    )
    return hotel_agent



# Required for ADK discovery
root_agent = create_hotel_agent()