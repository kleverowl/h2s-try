"""Flight Concierge Agent A2A Service Entry Point."""

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

# Local agent imports (updated for flight_agent)
from flight_agent.agent import create_flight_agent
from flight_agent.agent_executor import FlightADKAgentExecutor

# Load environment variables from .env file
load_dotenv()

# Basic logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the application name as requested
FLIGHT_A2A_APP_NAME = "FLIGHT_a2a_app"


@click.command()
@click.option(
    "--host",
    "host",
    default=os.getenv("A2A_FLIGHT_HOST", "localhost"),
    show_default=True,
    help="Host for the Flight Concierge Agent server.",
)
@click.option(
    "--port",
    "port",
    default=int(os.getenv("A2A_FLIGHT_PORT", 8002)),
    show_default=True,
    type=int,
    help="Port for the Flight Concierge Agent server.",
)
def main(host: str, port: int) -> None:
    """Runs the Flight ADK Agent as an A2A service."""

    # Check for a required flight API key
    if not os.getenv("FLIGHT_API_KEY"):
        logger.warning(
            "FLIGHT_API_KEY environment variable not set. "
            "The agent might fail to fetch flight data."
        )

    # Define AgentSkills for the Flight Concierge Agent ✈️
    flight_search_skill = AgentSkill(
        id="flight_search",
        name="Search for Flights",
        description="Finds one-way or round-trip flights between two destinations for given dates.",
        tags=["flights", "search", "booking", "travel", "itinerary"],
        examples=[
            "Find flights from Mumbai to Delhi tomorrow",
            "Search for a round trip flight from Nashik to Bangalore next week for 2 adults",
            "What are the cheapest flights to Goa next month?",
        ],
    )

    flight_status_skill = AgentSkill(
        id="flight_status_check",
        name="Check Flight Status",
        description="Provides real-time status updates for a specific flight number, including delays and gate information.",
        tags=["flights", "status", "tracking", "real-time", "travel"],
        examples=[
            "What is the status of flight 6E 237?",
            "Is AI 805 from London on time?",
        ],
    )

    # Define the main AgentCard for the Flight Concierge
    agent_card = AgentCard(
        name="Flight Concierge Agent",
        description="An agent to search for flights, check flight status, and assist with travel planning.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=False, pushNotifications=False),
        skills=[flight_search_skill, flight_status_skill],
    )

    try:
        # Create the actual ADK Agent for flights
        adk_agent = create_flight_agent()

        # Initialize the ADK Runner
        runner = Runner(
            app_name=FLIGHT_A2A_APP_NAME,
            agent=adk_agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

        # Instantiate the AgentExecutor with the runner
        agent_executor = FlightADKAgentExecutor(
            agent=adk_agent, agent_card=agent_card, runner=runner
        )

    except Exception as e:
        logger.error(
            f"Failed to initialize Flight Agent components: {e}", exc_info=True
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

    logger.info(f"Starting Flight Concierge Agent server on http://{host}:{port}")
    logger.info(f"Agent Name: {agent_card.name}, Version: {agent_card.version}")
    if agent_card.skills:
        for skill in agent_card.skills:
            logger.info(f"  Skill: {skill.name} (ID: {skill.id}, Tags: {skill.tags})")

    # Run the Uvicorn server
    uvicorn.run(a2a_app.build(), host=host, port=port)


if __name__ == "__main__":
    main()