import json
import os
from google.adk.agents.llm_agent import Agent
from weather_agent.prompt import WEATHER_CONCIERGE_PROMPT

def create_weather_agent():
    weather_agent = Agent(
        model='gemini-2.0-flash',
        name='weather_agent',
        description='A weather information agent that helps users find accurate and up-to-date weather information for their specified locations.',
        instruction=WEATHER_CONCIERGE_PROMPT,
    )
    return weather_agent

# Required for ADK discovery
root_agent = create_weather_agent()