import json
import os
from google.adk.agents.llm_agent import Agent
from cab_agent.prompt import CAB_CONCIERGE_PROMPT

def create_cab_agent():
    cab_agent = Agent(
        model='gemini-2.0-flash',
        name='cab_agent',
        description='A cab booking agent that helps users book cab rides.',
        instruction=CAB_CONCIERGE_PROMPT,
    )
    return cab_agent



# Required for ADK discovery
root_agent = create_cab_agent()