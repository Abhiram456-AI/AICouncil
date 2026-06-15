import asyncio

from llm.openrouter_client import OpenRouterClient

from config.settings import MODEL_REGISTRY


llm = OpenRouterClient()


TEST_PROMPT = "Reply with exactly: WORKING"


async def test_model(role, model):

    try:

        result = await llm.generate(model, TEST_PROMPT)

        if isinstance(result, dict):

            text = result.get("content", "")

        else:

            text = result

        print(f"\n {role}")
        print(f" model: {model}")
        print(f" status: WORKING")

    except Exception as e:

        print(f"\n {role}")
        print(f" model: {model}")
        print(f" status: FAILED")
        print(f" error: {str(e)}")


async def main():

    print("\nChecking model availability...\n")

    tasks = []

    for role, model in MODEL_REGISTRY.items():

        tasks.append(test_model(role, model))

    await asyncio.gather(*tasks)


asyncio.run(main())