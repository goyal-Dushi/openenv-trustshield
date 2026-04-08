# TrustShield v1

TrustShield v1 is an OpenEnv-based Trust & Safety investigation environment for a dating / matrimonial app.
It turns a moderation case into a multi-step investigation benchmark where an AI agent must gather evidence, recognize risk, and choose the correct action.

## Problem statement

Dating and matrimonial platforms need more than binary spam filters. TrustShield tests whether an agent can:

- investigate suspicious profiles and chat behavior,
- gather evidence efficiently,
- and select the right moderation outcome.

## Why this environment matters

This environment is built for hackathons and RL research. It simulates real investigation workflows rather than a single spam classifier, making it a better benchmark for moderation decision-making.

## Skill being tested

- evidence collection
- risk prioritization
- moderation decision quality
- efficiency in investigation steps
- avoiding unnecessary escalation

## State, actions, and reward summary

- state: investigation case, risk flags, and raw profile/chat data
- observations: partial profile/chat summaries, revealed signals, step count, and reward feedback
- actions: review profile/chat, check identity/financial/off-platform risk, request human review, mark legit, flag suspicious, ban user
- reward: base step penalty plus bonuses for helpful checks and correct final decisions

## Local setup

This project uses `uv` for dependency management when available.

```bash
uv install
```

If you do not use `uv`, install dependencies manually in your Python environment.

## Run instructions

Start the API server locally:

```bash
uv run uvicorn app.server.app:app --host 127.0.0.1 --port 8000
```

Then open your browser or use the agents against:

```text
http://127.0.0.1:8000
```

## Docker instructions

Build the Docker image:

```bash
docker build -t trustshield-v1 .
```

Run the container:

```bash
docker run --rm -p 8000:8000 trustshield-v1
```

## Agents

- `python agents/random_agent.py` runs a random action agent against the local API.
- `python agents/rule_based_agent.py` runs a simple heuristic investigator that reviews evidence and chooses a final moderation action.

## Testing

Run the small pytest suite:

```bash
pytest
```

## Benchmark value

TrustShield v1 is an interesting benchmark because it rewards agents for learning when to investigate versus when to decide. It encourages reasoning over chat and profile evidence, not only classification.
