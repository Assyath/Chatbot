import logging
import os

from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

load_dotenv()
logging.basicConfig(level=logging.INFO)

provider = OpenAIProvider(
    base_url="https://api.rodiumai.io/v1",
    api_key=os.environ["RODIUMAI_API_KEY"],
)
agent = Agent(OpenAIChatModel("openai/gpt-4o-mini", provider=provider))
print(agent.run_sync("Dis bonjour en un mot").output)