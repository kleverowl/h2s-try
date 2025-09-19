import json
import os
from google.adk.agents.llm_agent import Agent
from flight_agent.prompt import FLIGHT_CONCIERGE_PROMPT

def create_flight_agent():
    flight_agent = Agent(
        model='gemini-2.0-flash',
        name='flight_agent',
        description='A flight booking agent that helps users find and book flights based on their preferences.',
        instruction=FLIGHT_CONCIERGE_PROMPT,
    )
    return flight_agent



# Required for ADK discovery
root_agent = create_flight_agent()