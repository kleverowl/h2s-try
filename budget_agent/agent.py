import json
import os
from google.adk.agents.llm_agent import Agent
from budget_agent.prompt import BUDGET_CONCIERGE_PROMPT

def create_budget_agent():
    budget_agent = Agent(
        model='gemini-2.0-flash',
        name='budget_agent',
        description='A budget management agent that helps users track their travel expenses.',
        instruction=BUDGET_CONCIERGE_PROMPT,
    )
    return budget_agent



# Required for ADK discovery
root_agent = create_budget_agent()