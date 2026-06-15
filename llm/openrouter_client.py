import httpx
import asyncio
from config.settings import OPENROUTER_API_KEY


class OpenRouterClient:

    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    # fallback models if primary is rate-limited
    FALLBACK_REGISTRY = {

    "analyst": [
        "google/gemma-4-31b-it:free",          # heavier Gemma, vision+tools, quality 65
        "qwen/qwen3-next-80b-a3b-instruct:free", # 262K context, tools, quality 33
        "nvidia/nemotron-nano-9b-v2:free",      # lightweight, low latency, quality 24
    ],

    "reasoner_primary": [
        "openai/gpt-oss-20b:free",              # smaller GPT-OSS sibling, quality 41
        "nvidia/nemotron-3-super-120b-a12b:free", # high quality 60, 1M context
        "meta-llama/llama-3.3-70b-instruct:free", # solid general fallback, quality 24
    ],

    "reasoner_fast": [
        "nvidia/nemotron-nano-9b-v2:free",      # very fast, 128K context, quality 24
        "meta-llama/llama-3.2-3b-instruct:free", # tiny/fast, quality 16
        "openai/gpt-oss-20b:free",               # if speed matters less than quality
    ],

    "critic": [
        "nvidia/nemotron-3-super-120b-a12b:free", # strong general critic, quality 60
        "openai/gpt-oss-120b:free",               # large reasoning model as backup critic
        "qwen/qwen3-next-80b-a3b-instruct:free",  # broad context, decent tools
    ],

    "technical_validator": [
        "openai/gpt-oss-120b:free",             # strong general+code reasoning fallback
        "nvidia/nemotron-3-super-120b-a12b:free", # capable fallback if coder model down
        "meta-llama/llama-3.3-70b-instruct:free", # last resort for code review tasks
    ],

    "moderator": [
        "openrouter/owl-alpha",                 # agentic, 1M context, strong synthesis
        "openai/gpt-oss-120b:free",             # large reasoning model, good summarizer
        "qwen/qwen3-next-80b-a3b-instruct:free", # decent fallback if both above busy
    ],
}

    def get_fallback_chain(self, model):

        for role, models in self.FALLBACK_REGISTRY.items():
            if model in models:
                return models

        return []

    async def _make_request(self, model, prompt):

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=15.0,
                read=45.0,
                write=15.0,
                pool=15.0
            )
        ) as client:

            response = await client.post(

                self.BASE_URL,

                headers={

                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",

                    "Content-Type": "application/json",

                    "HTTP-Referer": "http://localhost",

                    "X-Title": "AI Council"

                },

                json={

                    "model": model,

                    "messages": [

                        {

                            "role": "user",

                            "content": prompt

                        }

                    ]

                }

            )

            if response.status_code != 200:

                return {

                    "error": {

                        "message": f"HTTP {response.status_code}"

                    }

                }

            try:

                return response.json()

            except Exception:

                return {

                    "error": {

                        "message": "Invalid response"

                    }

                }


    async def generate(self, model, prompt):

        models_to_try = [model]

        if len(models_to_try) == 1:

            generic_fallbacks = [
                "openai/gpt-oss-20b:free",
                "nvidia/nemotron-3-super-120b-a12b:free",
                "google/gemma-4-31b-it:free"
            ]

            for fallback in generic_fallbacks:
                if fallback != model:
                    models_to_try.append(fallback)

        for fallback_models in self.FALLBACK_REGISTRY.values():
            if model in fallback_models:
                continue

        role_fallbacks = self.get_fallback_chain(model)

        for fallback in role_fallbacks:
            if fallback != model:
                models_to_try.append(fallback)

        for attempt, model_name in enumerate(models_to_try):

            try:

                data = await self._make_request(model_name, prompt)

                if "choices" in data:

                    return data["choices"][0]["message"]["content"]

                # if API returns structured error
                if "error" in data:

                    print(f"\nModel failed: {model_name}")

                    print(data["error"]["message"])

            except Exception as e:

                print(f"\nException with {model_name}: {str(e)}")

            # exponential backoff
            wait_time = 2 ** attempt

            print(f"Retrying in {wait_time}s...\n")

            await asyncio.sleep(wait_time)

        raise RuntimeError(
            f"All models failed or rate-limited. Tried: {models_to_try}"
        )