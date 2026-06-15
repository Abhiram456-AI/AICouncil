import asyncio
from llm.openrouter_client import OpenRouterClient
from config.settings import MODEL_REGISTRY

llm = OpenRouterClient()

async def test():

    model = MODEL_REGISTRY["reasoner_fast"]

    prompt = "Reply with: API connection successful"

    result = await llm.generate(model, prompt)

    print("\nMODEL:", model)
    print("\nRESPONSE:")
    print(result)

asyncio.run(test())