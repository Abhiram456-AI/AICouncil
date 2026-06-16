# AI Council
 
A multi-agent AI deliberation system for consensus-driven decision making.
 
Instead of querying a single LLM, AI Council routes a query through a small "parliament" of specialized agents — each played by a different model via [OpenRouter](https://openrouter.ai) — that reason independently, critique each other, revise their positions, and converge (or explicitly disagree) on a final answer with a quantified consensus score.
 
## How it works
 
The pipeline is **adaptive**: the number of agents involved depends on how complex the query is, as judged by the system itself.
 
1. **Analyst** (Chief Strategist) reads the query first and classifies it as `low`, `medium`, or `high` complexity, and recommends a minimum council size.
2. **Routing**:
   - `low` → only the **Primary Reasoner** responds.
   - `medium` → **Primary Reasoner** + **Alternative Reasoner** (an "opposition thinker" tasked with avoiding groupthink) run in parallel.
   - `high` → the above plus a **Technical Validator** (feasibility/engineering review) — all three run in parallel.
3. **Critic** (Devil's Advocate) reviews all positions — but only if there's more than one viewpoint to critique. Single-viewpoint (`low`) queries skip this step.
4. **Consensus scoring (round 1)** — see below.
5. **Evidence step (conditional)**: if consensus is below `0.6` and multiple reasoners participated, the Primary Reasoner is asked to assess factual support for the claims.
6. **Revision round**: every active reasoner/validator revisits their position given the critic's feedback and the consensus score, choosing to `maintain`, `refine`, or `revise`.
7. **Consensus scoring (round 2)** on the revised positions. Above `0.75` is flagged as high consensus.
8. **Moderator** (Speaker of Parliament) synthesizes all revised positions, the critic's notes, and the consensus history into a final answer — preserving minority opinions rather than averaging them away.
Every step is logged to a discussion log, and the agreement history across both scoring rounds is returned alongside the final answer.
 
## Consensus engine
 
The consensus score is a weighted blend of four independent signals (`agreement.py`):
 
| Signal | Weight | What it measures |
|---|---|---|
| Cluster agreement | 20% | Fraction of agents landing in the largest stance cluster |
| Weighted semantic similarity | 40% | TF-IDF cosine similarity between reasoning texts, adjusted by stance agreement, confidence alignment, and numeric probability-range overlap |
| Stance agreement | 30% | Pairwise agreement on directional stance (positive/negative/neutral), detected via pattern matching |
| Confidence alignment | 10% | How closely agents' stated confidence levels align with each other |
 
This is computed independently of any single LLM's self-report — it's derived entirely from the text and structured fields each agent returns.
 
## Resilience
 
Each agent role has a primary model and a per-role fallback chain (`config/settings.py`). If a model call times out (90s) or errors, `call_agent` walks the fallback chain before giving up. If the moderator fails entirely, the system still returns the council's consensus with a fallback summary rather than erroring out.
 
## Project structure
 
```
.
├── main.py                  # FastAPI entry point (/council endpoint)
├── config/
│   └── settings.py           # Model registry + fallback chains, API key loading
├── llm/
│   └── openrouter_client.py  # OpenRouter API client with retry/fallback
├── council/
│   ├── orchestrator.py       # Core pipeline (routing, rounds, scoring)
│   ├── agreement.py           # Consensus scoring engine
│   ├── prompts.py             # Agent role prompts/identities
│   └── state.py               # Council state container + event logging
├── test_council.py          # End-to-end run with full output dump
├── test_llm_connection.py   # Single-model connectivity check
└── testing_models.py        # Checks every model in MODEL_REGISTRY is reachable
```
 
## Setup
 
```bash
git clone https://github.com/Abhiram456-AI/AICouncil.git
cd AICouncil
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```
 
Create a `.env` file in the project root:
 
```
OPENROUTER_API_KEY=your_key_here
```
 
## Running
 
**End-to-end test** (runs a full council deliberation and prints every stage — routing decision, agent outputs, agreement matrix, consensus score, agreement history, revision history, final answer):
 
```bash
python test_council.py
```
 
**Check model availability** (verifies every model in the registry responds):
 
```bash
python testing_models.py
```
 
**Run as an API**:
 
```bash
uvicorn main:app --reload
```
 
```bash
curl -X POST http://127.0.0.1:8000/council \
  -H "Content-Type: application/json" \
  -d '{"query": "Will AGI arrive before 2035?"}'
```
 
## Example
 
Query: `Will AGI arrive before 2035?`
 
The system routes this as `high` complexity (forecasting), so all three reasoners plus the critic and revision round run. A typical output includes:
 
```json
{
  "complexity": "high",
  "council_size": 3,
  "consensus_score": 0.525,
  "agreement_history": [
    {"round": 2, "score": 0.496},
    {"round": 3, "score": 0.525}
  ],
  "final_answer": {
    "final_answer": "AGI is unlikely to arrive before 2035.",
    "consensus_score": 0.525,
    "minority_opinions": ["..."]
  }
}
```
 
Note the score moves from round 2 (initial positions) to round 3 (post-revision) — this is the system actually measuring whether critique changed anyone's mind, not just reporting a static number.
 
## Default models (via OpenRouter, free tier)
 
| Role | Model |
|---|---|
| Analyst | Gemma 4 26B |
| Primary Reasoner | GPT-OSS 120B |
| Alternative Reasoner | Nemotron Nano 30B |
| Critic | Owl Alpha |
| Technical Validator | Qwen3 Coder |
| Moderator | Nemotron Super 120B |
 
Each role has a configured fallback chain in `config/settings.py` used if the primary model is rate-limited or unavailable.
 
## Research motivation
 
This project explores whether structured deliberation among heterogeneous models — independent reasoning, adversarial critique, and an evidence-driven revision loop — produces more reliable, better-calibrated outputs than a single model's first response, and whether disagreement between models can be measured in a way that's meaningful rather than cosmetic.
