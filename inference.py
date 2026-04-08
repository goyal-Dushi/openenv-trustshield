from __future__ import annotations

import json
from statistics import mean

from app.server.environment import TrustShieldEnvironment
from app.tasks import list_tasks
from grader import grade_episode


def choose_action(state: dict, observation: dict) -> str:
    """
    Deterministic baseline policy for TrustShield v1.
    """

    signals = " ".join(observation.get("revealed_signals", [])).lower()
    profile = observation.get("visible_profile_summary", "").lower()
    chat = observation.get("visible_chat_summary", "").lower()

    step_count = observation.get("step_count", 0)

    # Always investigate profile first
    if not state.get("profile_reviewed", False):
        return "review_profile"

    # Then investigate chat
    if not state.get("chat_reviewed", False):
        return "review_chat"

    # Financial scam indicators -> strongest action
    if any(term in signals or term in chat for term in [
        "paytm", "upi", "investment", "money", "bank", "transfer", "₹"
    ]):
        return "ban_user"

    # Off-platform / impersonation indicators
    if any(term in signals or term in chat for term in [
        "whatsapp", "telegram", "outside the app", "phone number", "off-platform"
    ]):
        if not state.get("offplatform_risk_checked", False):
            return "check_offplatform_risk"
        if not state.get("identity_risk_checked", False):
            return "check_identity_risk"
        return "ban_user"

    # Financial check if anything suspicious
    if any(term in signals or term in chat for term in [
        "urgent", "special opportunity", "verify identity", "uncle works", "family introduction"
    ]):
        if not state.get("financial_risk_checked", False):
            return "check_financial_risk"

    # Borderline / ambiguous
    if any(term in signals or term in profile for term in [
        "inconsistencies", "low confidence", "differ", "generic", "scripted", "rehearsed"
    ]):
        if not state.get("identity_risk_checked", False):
            return "check_identity_risk"
        if not state.get("human_review_requested", False) and step_count >= 3:
            return "request_human_review"
        return "flag_suspicious"

    # If nothing suspicious after enough checks -> legit
    return "mark_legit"


def run_single_task(task_name: str) -> dict:
    env = TrustShieldEnvironment(seed=42)

    observation = env.reset(task_name=task_name)

    print(
        f"[START] task={task_name} case_id={observation.case_id} "
        f"step_count={observation.step_count} status={observation.case_status}"
    )

    final_observation = observation

    while True:
        state = env.state.model_dump()
        action = choose_action(state, final_observation.model_dump())

        print(
            f"[STEP] task={task_name} "
            f"step={final_observation.step_count + 1} "
            f"action={action}"
        )

        final_observation = env.step(action)

        print(
            f"[STEP] task={task_name} "
            f"result_reward={final_observation.reward:.2f} "
            f"done={final_observation.done} "
            f"last_action={final_observation.last_action}"
        )

        if final_observation.done:
            break

    final_state = env.state.model_dump()
    grade = grade_episode(
        task_name=task_name,
        final_state=final_state,
        final_observation=final_observation.model_dump(),
    )

    print(
        f"[END] task={task_name} "
        f"score={grade['score']:.4f} "
        f"passed={grade['passed']} "
        f"steps={final_state.get('step_count', 0)} "
        f"decision={final_observation.last_action}"
    )

    return {
        "task_name": task_name,
        "case_id": final_observation.case_id,
        "score": grade["score"],
        "passed": grade["passed"],
        "steps": final_state.get("step_count", 0),
        "decision": final_observation.last_action,
        "reasoning": grade["reasoning"],
    }


def main() -> None:
    tasks = list_tasks()
    results = [run_single_task(task_name) for task_name in tasks]

    avg_score = round(mean(result["score"] for result in results), 4)
    pass_rate = round(sum(1 for result in results if result["passed"]) / len(results), 4)

    summary = {
        "num_tasks": len(results),
        "avg_score": avg_score,
        "pass_rate": pass_rate,
        "results": results,
    }

    print("\n=== FINAL SUMMARY ===")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()