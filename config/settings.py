import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL_REGISTRY = {

    "analyst":
        "google/gemma-4-26b-a4b-it:free",

    "reasoner_primary":
        "openai/gpt-oss-120b:free",

    "reasoner_fast":
        "nvidia/nemotron-3-nano-30b-a3b:free",

    "critic":
        "openrouter/owl-alpha",

    "technical_validator":
        "qwen/qwen3-coder:free",

    "moderator":
        "nvidia/nemotron-3-super-120b-a12b:free"
}

FALLBACK_REGISTRY = {
    "analyst": [
        "google/gemma-4-31b-it:free",
        "qwen/qwen3-next-80b-a3b-instruct:free",
        "nvidia/nemotron-nano-9b-v2:free",
    ],

    "reasoner_primary": [
        "openai/gpt-oss-20b:free",
        "nvidia/nemotron-3-super-120b-a12b:free",
        "meta-llama/llama-3.3-70b-instruct:free",
    ],

    "reasoner_fast": [
        "nvidia/nemotron-nano-9b-v2:free",
        "meta-llama/llama-3.2-3b-instruct:free",
        "openai/gpt-oss-20b:free",
    ],

    "critic": [
        "nvidia/nemotron-3-super-120b-a12b:free",
        "openai/gpt-oss-120b:free",
        "qwen/qwen3-next-80b-a3b-instruct:free",
    ],

    "technical_validator": [
        "openai/gpt-oss-120b:free",
        "nvidia/nemotron-3-super-120b-a12b:free",
        "meta-llama/llama-3.3-70b-instruct:free",
    ],

    "moderator": [
        "openrouter/owl-alpha",
        "openai/gpt-oss-120b:free",
        "qwen/qwen3-next-80b-a3b-instruct:free",
    ],
}