import json
import os
from google.adk.agents.llm_agent import Agent
from activity_agent.prompt import ACTIVITY_CONCIERGE_PROMPT

def create_activity_agent():
    activity_agent = Agent(
        model='gemini-2.0-flash',
        name='activity_agent',
        description='An activity booking agent that helps users find and book activities based on their preferences.',
        instruction=ACTIVITY_CONCIERGE_PROMPT,
    )
    return activity_agent



# Required for ADK discovery
root_agent = create_activity_agent()