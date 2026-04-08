---
title: TrustShield v1
emoji: 🛡️
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
license: mit
---

# TrustShield v1

TrustShield v1 is an **OpenEnv-based Trust & Safety investigation benchmark** for a dating / matrimonial platform.

Instead of treating moderation as a simple binary spam classification task, this environment models it as a **multi-step decision-making problem**:

- inspect a user profile,
- review chat behavior,
- uncover hidden risk signals,
- and choose the correct moderation action.

It is designed for **benchmarking agents**, **rule-based systems**, and future **AI moderation policies**.

---

## Overview

Moderation on dating and matrimonial apps often requires more than detecting obvious spam.

A suspicious user may:

- push the conversation off-platform,
- request money,
- manipulate emotions,
- impersonate family or identity,
- or appear mostly normal while still being risky.

TrustShield simulates this moderation workflow as an environment where a policy must decide:

> **What should I investigate next, and when do I take action?**

---

## What this environment evaluates

TrustShield v1 tests whether a system can:

- gather relevant evidence efficiently,
- identify risk categories,
- avoid unnecessary or repeated investigation,
- and select the right moderation outcome.

This makes it closer to a **decision-making benchmark** than a traditional classifier.

---

## Benchmark objective

The goal is to solve each moderation case by balancing:

- **investigation quality**
- **decision correctness**
- **efficiency**
- **risk awareness**

An ideal policy should:

- inspect only what is necessary,
- uncover meaningful warning signals,
- and make the correct final moderation decision.

---

## Environment design

Each episode represents **one moderation case**.

The environment exposes only **partial information initially**, and more evidence is revealed when the agent takes investigative actions.

### Initial visible evidence

An agent begins with:

- visible profile summary
- visible chat summary
- a small number of revealed signals
- current step count
- case status

### Hidden evidence

Additional risk indicators can be uncovered through actions such as:

- reviewing the profile
- reviewing the chat
- checking identity risk
- checking financial scam risk
- checking off-platform movement risk

---

## Action space

The agent can take the following actions:

### Investigation actions

- `review_profile`
- `review_chat`
- `check_identity_risk`
- `check_financial_risk`
- `check_offplatform_risk`

### Final moderation actions

- `mark_legit`
- `flag_suspicious`
- `ban_user`
- `request_human_review`

---

## Reward design

The reward structure encourages useful investigation and penalizes poor moderation behavior.

### Positive reward examples

- uncovering relevant hidden evidence
- selecting the correct final moderation outcome
- resolving a case efficiently

### Negative reward examples

- repeated or redundant investigation
- unnecessary steps
- incorrect final moderation decisions

This makes the benchmark suitable for:

- rule-based baselines
- planning agents
- RL-style experimentation
- LLM-powered decision systems

---

## Cases included

TrustShield v1 currently includes **6 handcrafted moderation cases** across different difficulty levels.

### Case categories covered

- financial scam
- impersonation / identity mismatch
- off-platform lure
- emotional manipulation
- suspicious-but-uncertain behavior
- legitimate user behavior

### Difficulty levels

- **easy**
- **medium**
- **hard**

---

## Example benchmark cases

Examples include users who:

- ask for money through emotional trust-building,
- push users to WhatsApp or Telegram too early,
- present inconsistent family / profile / chat claims,
- or appear mostly legitimate with subtle ambiguity.

This allows the environment to test not only **obvious spam detection**, but also **moderation judgment**.

---

## Project structure

```text
trustshield-v1/
├── app/
│   ├── models.py
│   ├── tasks.py
│   └── server/
│       ├── app.py
│       └── environment.py
├── agents/
│   ├── random_agent.py
│   └── rule_based_agent.py
├── tests/
│   └── test_environment.py
├── grader.py
├── inference.py
├── Dockerfile
├── pyproject.toml
└── README.md