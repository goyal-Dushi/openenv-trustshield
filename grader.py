from __future__ import annotations

from typing import Any


def grade_episode(task_name: str, final_state: dict[str, Any], final_observation: dict[str, Any]) -> dict[str, Any]:
    """
    Returns normalized score in [0.0, 1.0] for checking compatibility.
    """

    ground_truth = final_state.get("ground_truth")
    ideal_resolution = final_state.get("ideal_resolution")
    steps_taken = final_state.get("step_count", 0)
    last_action = final_observation.get("last_action")
    revealed_signals = final_observation.get("revealed_signals", [])

    score = 0.0
    reasoning: list[str] = []

    # 1. Final decision correctness (largest component)
    if last_action == ideal_resolution:
        score += 0.70
        reasoning.append("Final decision matches ideal resolution.")
    elif ground_truth == "spam" and last_action == "flag_suspicious":
        score += 0.45
        reasoning.append("Partially correct: spam was not banned but was flagged.")
    elif ground_truth == "suspicious" and last_action == "ban_user":
        score += 0.40
        reasoning.append("Conservative moderation choice for suspicious user.")
    elif ground_truth == "legit" and last_action == "flag_suspicious":
        score += 0.20
        reasoning.append("Cautious but incorrect moderation action.")
    else:
        reasoning.append("Final decision was incorrect.")

    # 2. Investigation quality
    signal_bonus = min(len(revealed_signals), 4) * 0.05
    score += signal_bonus
    reasoning.append(f"Collected {len(revealed_signals)} revealed signals.")

    # 3. Efficiency bonus
    if steps_taken <= 3:
        score += 0.10
        reasoning.append("Efficient resolution.")
    elif steps_taken <= 5:
        score += 0.05
        reasoning.append("Reasonably efficient resolution.")
    else:
        reasoning.append("Resolution used many steps.")

    # 4. Bonus for not rushing hard cases
    difficulty = final_state.get("difficulty")
    if difficulty == "hard" and steps_taken >= 2:
        score += 0.05
        reasoning.append("Hard case received some investigation before final decision.")

    score = max(0.0, min(1.0, round(score, 4)))

    return {
        "task_name": task_name,
        "score": score,
        "passed": score >= 0.6,
        "reasoning": reasoning,
    }