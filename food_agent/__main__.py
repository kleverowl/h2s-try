"""Food Concierge Agent A2A Service Entry Point."""

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

# Local agent imports (updated for food_agent)
from food_agent.agent import create_food_agent
from food_agent.agent_executor import FoodADKAgentExecutor

# Load environment variables from .env file
load_dotenv()

# Basic logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the application name as requested
FOOD_A2A_APP_NAME = "FOOD_a2a_app"


@click.command()
@click.option(
    "--host",
    "host",
    default=os.getenv("A2A_FOOD_HOST", "localhost"),
    show_default=True,
    help="Host for the Food Concierge Agent server.",
)
@click.option(
    "--port",
    "port",
    default=int(os.getenv("A2A_FOOD_PORT", 8003)),
    show_default=True,
    type=int,
    help="Port for the Food Concierge Agent server.",
)
def main(host: str, port: int) -> None:
    """Runs the Food ADK Agent as an A2A service."""

    # Check for a required food API key
    if not os.getenv("FOOD_API_KEY"):
        logger.warning(
            "FOOD_API_KEY environment variable not set. "
            "The agent might fail to fetch food data."
        )

    # Define AgentSkills for the Food Concierge Agent 🍔
    food_search_skill = AgentSkill(
        id="food_search",
        name="Search for Restaurants",
        description="Finds restaurants based on cuisine and location.",
        tags=["restaurants", "reservations", "dining", "dining plan"],
        examples=[
            "Find Italian restaurants in New York",
            "Find a good place for sushi nearby",
            "What are the best-rated vegan restaurants in London?",
        ],
    )

    restaurant_availability_skill = AgentSkill(
        id="restaurant_availability_check",
        name="Check Restaurant Availability",
        description="Checks if a restaurant has tables available for a specific time and party size.",
        tags=["restaurants", "availability", "reservations", "real-time", "dining"],
        examples=[
            "Is there a table for 2 at The Ivy at 8 PM tonight?",
            "Can I book a table for 4 at Dishoom tomorrow at 7 PM?",
        ],
    )

    # Define the main AgentCard for the Food Concierge
    agent_card = AgentCard(
        name="Food Concierge Agent",
        description="An agent to search for restaurants, check availability, and assist with dining planning.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=False, pushNotifications=False),
        skills=[food_search_skill, restaurant_availability_skill],
    )

    try:
        # Create the actual ADK Agent for food
        adk_agent = create_food_agent()

        # Initialize the ADK Runner
        runner = Runner(
            app_name=FOOD_A2A_APP_NAME,
            agent=adk_agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

        # Instantiate the AgentExecutor with the runner
        agent_executor = FoodADKAgentExecutor(
            agent=adk_agent, agent_card=agent_card, runner=runner
        )

    except Exception as e:
        logger.error(
            f"Failed to initialize Food Agent components: {e}", exc_info=True
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

    logger.info(f"Starting Food Concierge Agent server on http://{host}:{port}")
    logger.info(f"Agent Name: {agent_card.name}, Version: {agent_card.version}")
    if agent_card.skills:
        for skill in agent_card.skills:
            logger.info(f"  Skill: {skill.name} (ID: {skill.id}, Tags: {skill.tags})")

    # Run the Uvicorn server
    uvicorn.run(a2a_app.build(), host=host, port=port)


if __name__ == "__main__":
    main()