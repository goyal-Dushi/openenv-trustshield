from __future__ import annotations

import asyncio
import json
import os
import re
import textwrap
from typing import List, Optional

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from app.server.environment import TrustShieldEnvironment
from app.tasks import list_tasks
from grader import grade_episode

# =========================
# Required env variables
# =========================
HF_TOKEN = os.getenv("HF_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct")
TASK_NAME = os.getenv("TRUSTSHIELD_TASK")  # optional single-task run
BENCHMARK = os.getenv("TRUSTSHIELD_BENCHMARK", "trustshield")
MAX_STEPS = 8
TEMPERATURE = 0.2
MAX_TOKENS = 220

VALID_ACTIONS = [
    "review_profile",
    "review_chat",
    "check_identity_risk",
    "check_financial_risk",
    "check_offplatform_risk",
    "request_human_review",
    "mark_legit",
    "flag_suspicious",
    "ban_user",
]

SUCCESS_SCORE_THRESHOLD = 0.65  # can tune this later

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are TrustShield, a trust & safety moderation investigator for a dating / matrimonial platform.

    Your job is to investigate user cases and choose the single best NEXT action.

    Available actions:
    - review_profile
    - review_chat
    - check_identity_risk
    - check_financial_risk
    - check_offplatform_risk
    - request_human_review
    - mark_legit
    - flag_suspicious
    - ban_user

    Investigation policy:
    1. Prefer investigation actions before final decisions when evidence is incomplete.
    2. Use ban_user ONLY for strong evidence of scam, fraud, impersonation, spam, or malicious behavior.
    3. Use flag_suspicious for suspicious but not fully proven abuse.
    4. Use mark_legit when the evidence is clean or only weakly concerning.
    5. Use request_human_review for hard, ambiguous, or low-confidence cases.
    6. Avoid repeated actions.
    7. Do not over-penalize users based on weak or incomplete evidence.
    8. If a case appears mostly safe but slightly uncertain, prefer request_human_review or mark_legit over ban_user.

    Output rules:
    - Return EXACTLY one action string
    - No explanation
    - No JSON
    - No markdown

    Critical rule:
    - Do NOT ban users unless there is strong evidence of scam, impersonation, or financial abuse.
    - Ambiguous, generic, or rehearsed profiles are NOT sufficient reason to ban.
    - In uncertain cases, prefer request_human_review.
    """
).strip()


# =========================================================
# Logging helpers (MANDATORY HACKATHON FORMAT)
# =========================================================
def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


# =========================================================
# Prompt builder
# =========================================================
def build_user_prompt(
    task_name: str,
    step: int,
    observation: dict,
    state: dict,
    history: List[str],
) -> str:
    history_block = "\n".join(history[-5:]) if history else "None"

    return textwrap.dedent(
        f"""
        TASK: {task_name}
        STEP: {step}

        CURRENT OBSERVATION:
        case_id: {observation.get("case_id")}
        visible_profile_summary: {observation.get("visible_profile_summary")}
        visible_chat_summary: {observation.get("visible_chat_summary")}
        revealed_signals: {observation.get("revealed_signals")}
        step_count: {observation.get("step_count")}
        done: {observation.get("done")}
        case_status: {observation.get("case_status")}
        last_reward: {observation.get("reward")}
        last_action: {observation.get("last_action")}

        INTERNAL CASE METADATA:
        difficulty: {state.get("difficulty")}
        risk_types: {state.get("risk_types")}
        ground_truth: hidden
        ideal_resolution: hidden

        CURRENT INVESTIGATION STATE:
        profile_reviewed: {state.get("profile_reviewed")}
        chat_reviewed: {state.get("chat_reviewed")}
        identity_risk_checked: {state.get("identity_risk_checked")}
        financial_risk_checked: {state.get("financial_risk_checked")}
        offplatform_risk_checked: {state.get("offplatform_risk_checked")}
        human_review_requested: {state.get("human_review_requested")}

        RECENT ACTION HISTORY:
        {history_block}

        Choose the SINGLE best next action.

        Return ONLY one valid action string.
        """
    ).strip()


# =========================================================
# LLM action chooser
# =========================================================
def normalize_action(text: str) -> str:
    text = (text or "").strip().lower()
    text = text.replace('"', "").replace("'", "").strip()

    # exact match
    if text in VALID_ACTIONS:
        return text

    # extract any valid action mention
    for action in VALID_ACTIONS:
        if re.search(rf"\b{re.escape(action)}\b", text):
            return action

    return ""


def heuristic_fallback(state: dict, observation: dict) -> str:
    signals = " ".join(observation.get("revealed_signals", [])).lower()
    profile = observation.get("visible_profile_summary", "").lower()
    chat = observation.get("visible_chat_summary", "").lower()
    step_count = observation.get("step_count", 0)

    text = f"{signals} {profile} {chat}"

    # -----------------------------
    # 1) Always gather basic evidence first
    # -----------------------------
    if not state.get("profile_reviewed", False):
        return "review_profile"

    if not state.get("chat_reviewed", False):
        return "review_chat"

    # -----------------------------
    # 2) Strong financial scam signals
    # -----------------------------
    financial_terms = [
        "paytm", "upi", "investment", "money", "bank", "transfer",
        "₹", "loan", "send money", "financial help", "emergency funds"
    ]
    if any(term in text for term in financial_terms):
        if not state.get("financial_risk_checked", False):
            return "check_financial_risk"
        return "ban_user"

    # -----------------------------
    # 3) Off-platform / impersonation
    # -----------------------------
    offplatform_terms = [
        "whatsapp", "telegram", "outside the app", "phone number",
        "off-platform", "text me", "call me directly", "contact me elsewhere"
    ]
    impersonation_terms = [
        "identity mismatch", "inconsistent", "different photos",
        "fake", "pretending", "impersonation", "profile mismatch"
    ]

    has_offplatform = any(term in text for term in offplatform_terms)
    has_impersonation = any(term in text for term in impersonation_terms)

    if has_offplatform:
        if not state.get("offplatform_risk_checked", False):
            return "check_offplatform_risk"
        if has_impersonation and not state.get("identity_risk_checked", False):
            return "check_identity_risk"
        if has_impersonation:
            return "ban_user"
        return "flag_suspicious"

    # -----------------------------
    # 4) Emotional / manipulative / suspicious
    # -----------------------------
    suspicious_terms = [
        "urgent", "special opportunity", "verify identity", "family introduction",
        "emotional pressure", "love bombing", "manipulative", "scripted",
        "generic", "rehearsed", "low confidence", "uncertain", "inconsist"
    ]
    if any(term in text for term in suspicious_terms):
        if not state.get("identity_risk_checked", False):
            return "check_identity_risk"
        if not state.get("financial_risk_checked", False) and any(
            term in text for term in ["urgent", "special opportunity", "verify identity"]
        ):
            return "check_financial_risk"
        if not state.get("human_review_requested", False):
            return "request_human_review"
        return "flag_suspicious"

    # -----------------------------
    # 5) Hard legit / low-confidence legit
    # -----------------------------
    legit_terms = [
        "coherent", "not manipulative", "no asks for money",
        "consistent", "stable job", "stay on the app", "no financial red flags"
    ]
    legit_score = sum(1 for term in legit_terms if term in text)

    if legit_score >= 3:
        if step_count >= 2:
            return "mark_legit"

    # -----------------------------
    # 6) Conservative fallback
    # -----------------------------
    if not state.get("human_review_requested", False) and step_count >= 3:
        return "request_human_review"

    return "flag_suspicious"

def get_model_action(
    client: OpenAI,
    task_name: str,
    step: int,
    observation: dict,
    state: dict,
    history: List[str],
) -> str:
    if not OPENAI_AVAILABLE or client is None:
        return heuristic_fallback(state, observation)

    user_prompt = build_user_prompt(task_name, step, observation, state, history)

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=40,
            stream=False,
        )

        raw = (completion.choices[0].message.content or "").strip()
        action = normalize_action(raw)

        # invalid / empty model output
        if not action:
            return heuristic_fallback(state, observation)

        # prevent repeated actions
        if action == "review_profile" and state.get("profile_reviewed"):
            return heuristic_fallback(state, observation)
        if action == "review_chat" and state.get("chat_reviewed"):
            return heuristic_fallback(state, observation)
        if action == "check_identity_risk" and state.get("identity_risk_checked"):
            return heuristic_fallback(state, observation)
        if action == "check_financial_risk" and state.get("financial_risk_checked"):
            return heuristic_fallback(state, observation)
        if action == "check_offplatform_risk" and state.get("offplatform_risk_checked"):
            return heuristic_fallback(state, observation)
        if action == "request_human_review" and state.get("human_review_requested"):
            return heuristic_fallback(state, observation)
        # Safety rails against premature final actions
        if action == "ban_user":
            signals = " ".join(observation.get("revealed_signals", [])).lower()
            chat = observation.get("visible_chat_summary", "").lower()

            strong_financial = any(term in signals or term in chat for term in [
                "paytm", "upi", "investment", "money", "bank", "transfer", "loan", "crypto"
            ])

            strong_offplatform = any(term in signals or term in chat for term in [
                "whatsapp", "telegram", "phone number", "off-platform"
            ])

            strong_identity = any(term in signals for term in [
                "impersonation", "identity mismatch", "fake identity"
            ])

            # 🚨 If no strong signal → DO NOT BAN
            if not (strong_financial or strong_offplatform or strong_identity):
                return "request_human_review"

        if action == "mark_legit":
            if not state.get("profile_reviewed", False) or not state.get("chat_reviewed", False):
                return heuristic_fallback(state, observation)

        if action == "flag_suspicious":
            if not state.get("chat_reviewed", False):
                return heuristic_fallback(state, observation)

        return action

    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return heuristic_fallback(state, observation)


# =========================================================
# Single task runner
# =========================================================
def run_single_task(client: OpenAI, task_name: str) -> dict:
    env = TrustShieldEnvironment(seed=42)

    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    success = False
    score = 0.0

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    try:
        observation = env.reset(task_name=task_name)
        final_observation = observation

        for step in range(1, MAX_STEPS + 1):
            if final_observation.done:
                break

            state = env.state.model_dump()
            obs_dict = final_observation.model_dump()

            # First try strong deterministic policy
            policy_action = heuristic_fallback(state, obs_dict)

            # Use LLM only for ambiguous middle-stage decisions
            use_llm = (
                step >= 2
                and not final_observation.done
                and policy_action in {"flag_suspicious", "request_human_review", "mark_legit"}
            )

            if use_llm:
                action = get_model_action(
                    client=client,
                    task_name=task_name,
                    step=step,
                    observation=obs_dict,
                    state=state,
                    history=history,
                )
            else:
                action = policy_action

            error = None

            try:
                final_observation = env.step(action)
            except Exception as exc:
                error = str(exc)
                log_step(step=step, action=action, reward=0.00, done=True, error=error)
                break

            reward = final_observation.reward or 0.0
            done = final_observation.done

            rewards.append(reward)
            steps_taken = step

            log_step(step=step, action=action, reward=reward, done=done, error=error)

            history.append(
                f"Step {step}: action={action} reward={reward:.2f} "
                f"signals={final_observation.revealed_signals}"
            )

            if done:
                break

        final_state = env.state.model_dump()
        grade = grade_episode(
            task_name=task_name,
            final_state=final_state,
            final_observation=final_observation.model_dump(),
        )

        score = float(grade["score"])
        score = min(max(score, 0.0), 1.0)
        success = bool(grade["passed"])

        return {
            "task_name": task_name,
            "case_id": final_observation.case_id,
            "score": score,
            "passed": success,
            "steps": final_state.get("step_count", 0),
            "decision": final_observation.last_action,
            "reasoning": grade["reasoning"],
            "rewards": rewards,
        }

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


async def main() -> None:
    client = None

    if OPENAI_AVAILABLE and HF_TOKEN:
        try:
            client = OpenAI(
                base_url=API_BASE_URL,
                api_key=HF_TOKEN,
            )
        except Exception as e:
            print(f"[WARN] OpenAI init failed: {e}", flush=True)
            client = None
    else:
        print("[INFO] Running without OpenAI. Using heuristic policy.", flush=True)

    if TASK_NAME:
        tasks = [TASK_NAME]
    else:
        tasks = list_tasks()

    results = [run_single_task(client, task_name) for task_name in tasks]

    summary = {
        "num_tasks": len(results),
        "avg_score": round(sum(r["score"] for r in results) / len(results), 4) if results else 0.0,
        "pass_rate": round(sum(1 for r in results if r["passed"]) / len(results), 4) if results else 0.0,
        "results": results,
    }

    print("\n=== FINAL SUMMARY ===", flush=True)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    asyncio.run(main())