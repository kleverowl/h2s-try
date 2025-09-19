import json
import os
from google.adk.agents.llm_agent import Agent
from document_agent.prompt import DOCUMENT_CONCIERGE_PROMPT

def create_document_agent():
    document_agent = Agent(
        model='gemini-2.0-flash',
        name='document_agent',
        description='A document verification agent that helps users verify their travel documents.',
        instruction=DOCUMENT_CONCIERGE_PROMPT,
    )
    return document_agent



# Required for ADK discovery
root_agent = create_document_agent()