"""Weather Concierge Agent A2A Service Entry Point."""

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

# Local agent imports (updated for weather_agent)
from weather_agent.agent import create_weather_agent
from weather_agent.agent_executor import WeatherADKAgentExecutor

# Load environment variables from .env file
load_dotenv()

# Basic logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the application name as requested
WEATHER_A2A_APP_NAME = "WEATHER_a2a_app"


@click.command()
@click.option(
    "--host",
    "host",
    default=os.getenv("A2A_WEATHER_HOST", "localhost"),
    show_default=True,
    help="Host for the Weather Concierge Agent server.",
)
@click.option(
    "--port",
    "port",
    default=int(os.getenv("A2A_WEATHER_PORT", 8003)),
    show_default=True,
    type=int,
    help="Port for the Weather Concierge Agent server.",
)
def main(host: str, port: int) -> None:
    """Runs the Weather ADK Agent as an A2A service."""

    # Check for a required weather API key
    if not os.getenv("WEATHER_API_KEY"):
        logger.warning(
            "WEATHER_API_KEY environment variable not set. "
            "The agent might fail to fetch weather data."
        )

    # Define AgentSkills for the Weather Concierge Agent 🌦️
    current_weather_skill = AgentSkill(
        id="get_current_weather",
        name="Get Current Weather",
        description="Provides the current temperature and weather conditions for a specified location.",
        tags=["weather", "current", "temperature", "forecast", "conditions"],
        examples=[
            "What's the weather like in London right now?",
            "How hot is it in Dubai?",
            "Tell me the current weather in New York City",
        ],
    )

    weather_forecast_skill = AgentSkill(
        id="get_weather_forecast",
        name="Get Weather Forecast",
        description="Retrieves the weather forecast for the upcoming days for a given city.",
        tags=["weather", "forecast", "planning", "outlook", "rain"],
        examples=[
            "What is the forecast for Paris this weekend?",
            "Will it rain in Tokyo tomorrow?",
            "Give me the 5-day forecast for Sydney",
        ],
    )

    # Define the main AgentCard for the Weather Concierge
    agent_card = AgentCard(
        name="Weather Concierge Agent",
        description="An agent that provides current weather conditions and future forecasts for any location.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=False, pushNotifications=False),
        skills=[current_weather_skill, weather_forecast_skill],
    )

    try:
        # Create the actual ADK Agent for weather
        adk_agent = create_weather_agent()

        # Initialize the ADK Runner
        runner = Runner(
            app_name=WEATHER_A2A_APP_NAME,
            agent=adk_agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

        # Instantiate the AgentExecutor with the runner
        agent_executor = WeatherADKAgentExecutor(
            agent=adk_agent, agent_card=agent_card, runner=runner
        )

    except Exception as e:
        logger.error(
            f"Failed to initialize Weather Agent components: {e}", exc_info=True
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

    logger.info(f"Starting Weather Concierge Agent server on http://{host}:{port}")
    logger.info(f"Agent Name: {agent_card.name}, Version: {agent_card.version}")
    if agent_card.skills:
        for skill in agent_card.skills:
            logger.info(f"  Skill: {skill.name} (ID: {skill.id}, Tags: {skill.tags})")

    # Run the Uvicorn server
    uvicorn.run(a2a_app.build(), host=host, port=port)


if __name__ == "__main__":
    main()