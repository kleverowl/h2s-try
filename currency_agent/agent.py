import json
import os
from google.adk.agents.llm_agent import Agent
from currency_agent.prompt import CURRENCY_CONCIERGE_PROMPT

def create_currency_agent():
    currency_agent = Agent(
        model='gemini-2.0-flash',
        name='currency_agent',
        description='A currency conversion agent that helps users convert between different currencies.',
        instruction=CURRENCY_CONCIERGE_PROMPT,
    )
    return currency_agent



# Required for ADK discovery
root_agent = create_currency_agent()