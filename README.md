---
title: TrustShield 
emoji: 🛡️
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
license: mit
---

# TrustShield 

TrustShield  is an **OpenEnv-based Trust & Safety investigation benchmark** for a dating / matrimonial platform.

Instead of treating moderation as a simple binary spam classification task, this environment models it as a **multi-step decision-making problem**.

---

# 🧠 Environment Overview & Motivation

Moderation in dating and matrimonial platforms is inherently complex and **cannot be reduced to a single classification step**.

A suspicious user may:
- gradually build trust,
- shift conversations off-platform,
- request money,
- impersonate identity,
- or behave ambiguously.

Traditional systems fail because they:
- lack multi-step reasoning
- cannot handle uncertainty
- overfit to obvious spam signals

### 💡 Motivation

TrustShield reframes moderation as:

> **A sequential decision-making problem under uncertainty**

An agent must:
- decide **what to investigate**
- gather **incremental evidence**
- and choose the **correct moderation action**

This makes it suitable for:
- LLM agents
- rule-based systems
- reinforcement learning setups

---

# 🔍 Observation Space

Each step returns a structured observation:

### Initial Observation
- `case_id`
- `visible_profile_summary`
- `visible_chat_summary`
- `revealed_signals` (partial)
- `step_count`
- `done`
- `case_status`

### Dynamic Observation (after actions)
- additional `revealed_signals`
- updated `reward`
- `last_action`

👉 The environment starts **partially observable** and reveals more information over time.

---

# ⚙️ Action Space

The agent can take **9 discrete actions**:

## 🔎 Investigation Actions
- `review_profile`
- `review_chat`
- `check_identity_risk`
- `check_financial_risk`
- `check_offplatform_risk`

## 🚨 Final Moderation Actions
- `mark_legit`
- `flag_suspicious`
- `ban_user`
- `request_human_review`

👉 The agent must balance:
- exploration (gather evidence)
- exploitation (take correct action)

---

# 🎯 Task Descriptions & Difficulty Levels

TrustShield  includes **6 handcrafted cases** across 3 difficulty levels:

## 🟢 Easy
- **easy_spam_financial**
- **easy_spam_impersonation**

👉 Clear signals (money requests, impersonation)  
👉 Expected: **quick detection + correct ban**

---

## 🟡 Medium
- **medium_suspicious_emotional**
- **medium_suspicious_profile_mismatch**

👉 Mixed / ambiguous signals  
👉 Expected:  
- `flag_suspicious` OR  
- `request_human_review`

---

## 🔴 Hard
- **hard_legit_engineer**
- **hard_legit_teacher**

👉 Legitimate users with subtle ambiguity  
👉 Expected:
- `mark_legit` OR cautious review  
❗ Penalizes **false positives (wrong bans)**

---

# 🏗️ Environment Design

Each episode:
1. Starts with partial information
2. Agent performs step-by-step investigation
3. Evidence is revealed incrementally
4. Agent takes a final moderation decision

---

# 💰 Reward Design

The reward function encourages:

### ✅ Positive Rewards
- uncovering meaningful signals
- correct final decision
- efficient investigation

### ❌ Negative Rewards
- redundant steps
- unnecessary actions
- incorrect final decision (especially false bans)

---

# 🧪 Grading & Evaluation

Evaluation is handled by `grader.py`.

Each episode returns:

```json
{
  "score": 0.95,
  "passed": true,
  "reasoning": ["Final decision matches ideal resolution"]
}