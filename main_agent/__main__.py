"""Main Concierge Agent A2A Service Entry Point (Orchestrator)."""

import logging
import os

import click
import uvicorn

# A2A server imports
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from dotenv import load_dotenv

# ADK imports
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Local agent imports (updated for main_agent)
from main_agent.agent import create_root_agent
from main_agent.agent_executor import MainADKAgentExecutor

# Load environment variables from .env file
load_dotenv()

# Basic logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the application name for the main orchestrator
MAIN_A2A_APP_NAME = "MAIN_a2a_app"


@click.command()
@click.option(
    "--host",
    "host",
    default=os.getenv("A2A_MAIN_HOST", "localhost"),
    show_default=True,
    help="Host for the Main Concierge Agent server.",
)
@click.option(
    "--port",
    "port",
    default=int(os.getenv("A2A_MAIN_PORT", 8000)),
    show_default=True,
    type=int,
    help="Port for the Main Concierge Agent server.",
)
def main(host: str, port: int) -> None:
    """Runs the Main ADK Agent (Orchestrator) as an A2A service."""

    # Note: An orchestrator might not need its own API key if it only delegates tasks.
    # However, it might need keys to access other agents, which would be handled
    # within the agent's logic rather than checked at startup.
    logger.info("Initializing the main Main Concierge Agent (Orchestrator)...")

    # Define AgentSkills for the Main Concierge Agent 🗺️
    create_plan_skill = AgentSkill(
        id="create_travel_plan",
        name="Create a Travel Itinerary",
        description="Builds a complete travel itinerary by coordinating with other agents to find flights, check weather, and suggest activities.",
        tags=["itinerary", "planning", "orchestration", "travel", "concierge"],
        examples=[
            "Plan a 3-day trip to Goa next month",
            "Create a weekend itinerary for a trip from Mumbai to Delhi, including flights",
            "I want to go to Bangalore for 5 days, what should I do?",
        ],
    )

    # Define the main AgentCard for the Main Concierge
    agent_card = AgentCard(
        name="Main Concierge Agent (Orchestrator)",
        description="The main orchestrator agent that creates comprehensive travel plans by communicating with other specialized agents.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=False, pushNotifications=False),
        skills=[create_plan_skill],
    )

    try:
        # Create the actual ADK Agent for itinerary planning
        adk_agent = create_root_agent()

        # Initialize the ADK Runner
        runner = Runner(
            app_name=MAIN_A2A_APP_NAME,
            agent=adk_agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

        # Instantiate the AgentExecutor with the runner
        agent_executor = MainADKAgentExecutor(
            agent=adk_agent, agent_card=agent_card, runner=runner
        )

    except Exception as e:
        logger.error(
            f"Failed to initialize Main Agent components: {e}", exc_info=True
        )
        return

    # Set up the A2A request handler
    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor, task_store=InMemoryTaskStore()
    )

    # Create the A2A Starlette application
    a2a_app = A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )

    logger.info(f"Starting Main Concierge Agent server on http://{host}:{port}")
    logger.info(f"Agent Name: {agent_card.name}, Version: {agent_card.version}")
    if agent_card.skills:
        for skill in agent_card.skills:
            logger.info(f"  Skill: {skill.name} (ID: {skill.id}, Tags: {skill.tags})")

    # Run the Uvicorn server
    uvicorn.run(a2a_app.build(), host=host, port=port)


if __name__ == "__main__":
    main()