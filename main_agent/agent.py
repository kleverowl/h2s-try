from google.adk.agents.llm_agent import Agent
from main_agent.prompt import ROOT_AGENT_PROMPT
from main_agent.tools import TOOLS
from main_agent.memory import _load_precreated_plan

def create_root_agent():
    root_agent = Agent(
        model='gemini-1.5-flash-latest',
        name='main_agent',
        description='The Itinerary Agent, the central coordinator and master planner for creating personalized travel experiences by delegating tasks to specialized concierge agents.',
        instruction=ROOT_AGENT_PROMPT,
        tools=list(TOOLS.values()),
        before_agent_callback=[
                _load_precreated_plan
            ]
    )
    return root_agent


# Required for ADK discovery
root_agent = create_root_agent()
