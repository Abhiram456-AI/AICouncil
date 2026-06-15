from fastapi import FastAPI
from council.orchestrator import run_council

app = FastAPI()

@app.post("/council")
async def council_endpoint(payload: dict):

    query = payload["query"]

    result = await run_council(query)

    return result