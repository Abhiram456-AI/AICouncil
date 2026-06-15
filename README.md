# AI Council

A Multi-Agent AI Deliberation System for Consensus-Driven Decision Making
## Overview

AI Council is a multi-agent AI reasoning framework that simulates a
deliberative council of specialized AI agents.

Instead of relying on a single language model, AI Council routes a query
through multiple reasoning agents, a critic, and a moderator to generate
more robust, transparent, and explainable decisions.

The system is designed for:

- Complex reasoning tasks
- Strategic decision support
- Forecasting
- Technical validation
- Multi-perspective analysis
- AI consensus research
┌────────────────────┐
│    User Query      │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│      Analyst       │
│ Complexity Routing │
└─────────┬──────────┘
          │
          ▼
 ┌────────┼────────┐
 ▼        ▼        ▼

Reasoner  Reasoner  Technical
Primary   Fast      Validator

 └────────┼────────┘
          ▼

     Critic Agent
   Challenges Logic

          ▼

   Revision Round

          ▼

 Agreement Engine

          ▼

     Moderator

          ▼

   Final Decision

   ## Features

### Multi-Agent Deliberation

Specialized agents collaborate to solve problems.

### Dynamic Routing

Queries are routed based on complexity.

### Critic Review

A dedicated critic identifies:

- Hidden assumptions
- Logical flaws
- Weak evidence
- Alternative viewpoints

### Revision Rounds

Agents refine their positions after critique.

### Consensus Engine

Consensus is calculated using:

- Semantic similarity
- Confidence alignment
- Probability overlap
- Stance agreement

### Automatic Model Fallbacks

If a model becomes unavailable, fallback models are automatically used.

### Explainable Outputs

Every decision includes:

- Reasoning traces
- Agreement history
- Consensus metrics
- Minority opinions
## Example Query

```text
Will AGI arrive before 2035?
```

### Final Answer

```text
AGI is unlikely to arrive before 2035.

Consensus Probability:
10–30%

Consensus Score:
0.525
```

### Agreement History

```json
[
  {
    "round": 2,
    "score": 0.496
  },
  {
    "round": 3,
    "score": 0.525
  }
]
```
## Agreement Engine

AI Council evaluates agreement using multiple signals:

| Signal | Purpose |
|----------|----------|
| Semantic Similarity | Measures reasoning similarity |
| Confidence Alignment | Measures confidence convergence |
| Probability Overlap | Measures numerical agreement |
| Stance Agreement | Measures conclusion alignment |

These metrics are combined into a final consensus score.
## Default Model Configuration

| Role | Model |
|--------|--------|
| Analyst | Gemma 4 26B |
| Primary Reasoner | GPT OSS 120B |
| Fast Reasoner | Nemotron Nano 30B |
| Critic | Owl Alpha |
| Technical Validator | Qwen 3 Coder |
| Moderator | Nemotron Super 120B |
## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/AICouncil.git
cd AICouncil
```

Create virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create environment file:

```bash
cp .env.example .env
```

Add:

```env
OPENROUTER_API_KEY=YOUR_KEY
```
## Run

```bash
python test_council.py
```
## Research Motivation

AI Council investigates whether structured deliberation among
heterogeneous language models can improve reasoning quality,
reduce individual model bias, and produce more reliable decisions.

The project serves as an experimental platform for studying:

- AI consensus formation
- Multi-agent reasoning
- Confidence calibration
- Deliberative AI systems
