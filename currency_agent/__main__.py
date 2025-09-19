"""Currency Concierge Agent A2A Service Entry Point."""

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

# Local agent imports (updated for currency_agent)
from currency_agent.agent import create_currency_agent
from currency_agent.agent_executor import CurrencyADKAgentExecutor

# Load environment variables from .env file
load_dotenv()

# Basic logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the application name as requested
CURRENCY_A2A_APP_NAME = "CURRENCY_a2a_app"


@click.command()
@click.option(
    "--host",
    "host",
    default=os.getenv("A2A_CURRENCY_HOST", "localhost"),
    show_default=True,
    help="Host for the Currency Concierge Agent server.",
)
@click.option(
    "--port",
    "port",
    default=int(os.getenv("A2A_CURRENCY_PORT", 8008)),
    show_default=True,
    type=int,
    help="Port for the Currency Concierge Agent server.",
)
def main(host: str, port: int) -> None:
    """Runs the Currency ADK Agent as an A2A service."""

    # Define AgentSkills for the Currency Concierge Agent
    currency_conversion_skill = AgentSkill(
        id="currency_conversion",
        name="Convert Currency",
        description="Converts an amount from a source currency to a target currency.",
        tags=["currency", "conversion", "finance", "travel"],
        examples=[
            "Convert 100 USD to INR",
            "How much is 50 EUR in GBP?",
            "What is the exchange rate between AUD and JPY?",
        ],
    )

    # Define the main AgentCard for the Currency Concierge
    agent_card = AgentCard(
        name="Currency Concierge Agent",
        description="An agent to perform currency conversions.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=False, pushNotifications=False),
        skills=[currency_conversion_skill],
    )

    try:
        # Create the actual ADK Agent for currency
        adk_agent = create_currency_agent()

        # Initialize the ADK Runner
        runner = Runner(
            app_name=CURRENCY_A2A_APP_NAME,
            agent=adk_agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

        # Instantiate the AgentExecutor with the runner
        agent_executor = CurrencyADKAgentExecutor(
            agent=adk_agent, agent_card=agent_card, runner=runner
        )

    except Exception as e:
        logger.error(
            f"Failed to initialize Currency Agent components: {e}", exc_info=True
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

    logger.info(f"Starting Currency Concierge Agent server on http://{host}:{port}")
    logger.info(f"Agent Name: {agent_card.name}, Version: {agent_card.version}")
    if agent_card.skills:
        for skill in agent_card.skills:
            logger.info(f"  Skill: {skill.name} (ID: {skill.id}, Tags: {skill.tags})")

    # Run the Uvicorn server
    uvicorn.run(a2a_app.build(), host=host, port=port)


if __name__ == "__main__":
    main()