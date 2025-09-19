"""Budget Concierge Agent A2A Service Entry Point."""

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

# Local agent imports (updated for budget_agent)
from budget_agent.agent import create_budget_agent
from budget_agent.agent_executor import BudgetADKAgentExecutor

# Load environment variables from .env file
load_dotenv()

# Basic logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the application name as requested
BUDGET_A2A_APP_NAME = "BUDGET_a2a_app"


@click.command()
@click.option(
    "--host",
    "host",
    default=os.getenv("A2A_BUDGET_HOST", "localhost"),
    show_default=True,
    help="Host for the Budget Concierge Agent server.",
)
@click.option(
    "--port",
    "port",
    default=int(os.getenv("A2A_BUDGET_PORT", 8006)),
    show_default=True,
    type=int,
    help="Port for the Budget Concierge Agent server.",
)
def main(host: str, port: int) -> None:
    """Runs the Budget ADK Agent as an A2A service."""

    # Define AgentSkills for the Budget Concierge Agent
    budget_skill = AgentSkill(
        id="budget_management",
        name="Manage Budget",
        description="Tracks and manages travel expenses against a budget.",
        tags=["budget", "expenses", "finance", "travel", "itinerary"],
        examples=[
            "Track my expenses for the trip",
            "What is my remaining budget?",
            "Add a new expense to my budget",
        ],
    )

    # Define the main AgentCard for the Budget Concierge
    agent_card = AgentCard(
        name="Budget Concierge Agent",
        description="An agent to manage and track travel expenses.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=False, pushNotifications=False),
        skills=[budget_skill],
    )

    try:
        # Create the actual ADK Agent for budget
        adk_agent = create_budget_agent()

        # Initialize the ADK Runner
        runner = Runner(
            app_name=BUDGET_A2A_APP_NAME,
            agent=adk_agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

        # Instantiate the AgentExecutor with the runner
        agent_executor = BudgetADKAgentExecutor(
            agent=adk_agent, agent_card=agent_card, runner=runner
        )

    except Exception as e:
        logger.error(
            f"Failed to initialize Budget Agent components: {e}", exc_info=True
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

    logger.info(f"Starting Budget Concierge Agent server on http://{host}:{port}")
    logger.info(f"Agent Name: {agent_card.name}, Version: {agent_card.version}")
    if agent_card.skills:
        for skill in agent_card.skills:
            logger.info(f"  Skill: {skill.name} (ID: {skill.id}, Tags: {skill.tags})")

    # Run the Uvicorn server
    uvicorn.run(a2a_app.build(), host=host, port=port)


if __name__ == "__main__":
    main()