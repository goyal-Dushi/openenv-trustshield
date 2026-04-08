import random
import uuid
from typing import Any

from openenv.core.env_server import Environment as Env

from app.models import (
    TrustShieldAction,
    TrustShieldObservation,
    TrustShieldState,
)
from app.tasks import get_random_case, get_task_case

INVESTIGATION_ACTIONS = {
    "review_profile",
    "review_chat",
    "check_identity_risk",
    "check_financial_risk",
    "check_offplatform_risk",
    "request_human_review",
}
FINAL_DECISIONS = {"mark_legit", "flag_suspicious", "ban_user"}
MAX_STEPS = 8


class TrustShieldEnvironment(Env):
    def __init__(self, seed: int | None = None):
        super().__init__()
        self._state: TrustShieldState | None = None
        self._case: dict[str, Any] | None = None
        self._revealed_signals: list[str] = []
        self._seed = seed
        if seed is not None:
            random.seed(seed)

    @property
    def state(self) -> TrustShieldState:
        if self._state is None:
            raise ValueError("Environment has not been reset yet.")
        return self._state

    def reset(self, task_name: str | None = None) -> TrustShieldObservation:
        self._case = get_task_case(task_name) if task_name else get_random_case()
        self._revealed_signals = []

        self._state = TrustShieldState(
            episode_id=str(uuid.uuid4()),
            case_id=self._case["case_id"],
            ground_truth=self._case["ground_truth"],
            ideal_resolution=self._case["ideal_resolution"],
            difficulty=self._case["difficulty"],
            risk_types=self._case["risk_types"],
            step_count=0,
            done=False,
            profile_reviewed=False,
            chat_reviewed=False,
            identity_risk_checked=False,
            financial_risk_checked=False,
            offplatform_risk_checked=False,
            human_review_requested=False,
            profile=self._case["profile"],
            chat_history=self._case["chat_history"],
            signals=self._case["signals"],
        )

        self._reveal_initial_signals()
        return self._build_observation(last_action=None, reward=0.0)

    def _coerce_action(self, action: str | TrustShieldAction | dict[str, str]) -> TrustShieldAction:
        if isinstance(action, TrustShieldAction):
            return action
        if isinstance(action, dict):
            return TrustShieldAction.model_validate(action)
        return TrustShieldAction.model_validate({"action": action})

    def step(
        self,
        action: TrustShieldAction
    ) -> TrustShieldObservation:
        action_obj = self._coerce_action(action)
        if self._state is None:
            raise ValueError("Environment must be reset before stepping.")
        if self._state.done:
            raise ValueError("Episode already finished. Reset to start a new case.")

        self._state = self._state.model_copy(update={"step_count": self._state.step_count + 1, "done": False})
        reward = -0.5

        if action_obj.action in INVESTIGATION_ACTIONS:
            reward += self._handle_investigation_action(action_obj.action)
        else:
            reward += self._handle_final_decision(action_obj.action)
            self._state = self._state.model_copy(update={"done": True})

        if self._state.step_count >= MAX_STEPS and not self._state.done:
            self._state = self._state.model_copy(update={"done": True})

        observation = self._build_observation(last_action=action_obj.action, reward=reward)
        return observation

    def _reveal_initial_signals(self) -> None:
        if self._case is None:
            return
        profile_signals = self._case["signals"].get("profile", [])
        chat_signals = self._case["signals"].get("chat", [])
        if profile_signals:
            self._revealed_signals.append(profile_signals[0])
        if chat_signals:
            self._revealed_signals.append(chat_signals[0])

    def _reveal_signals(self, category: str) -> None:
        if self._case is None:
            return
        for signal in self._case["signals"].get(category, []):
            if signal not in self._revealed_signals:
                self._revealed_signals.append(signal)

    def _build_observation(self, last_action: str | None, reward: float) -> TrustShieldObservation:
        return TrustShieldObservation(
            case_id=self._state.case_id,
            visible_profile_summary=self._build_profile_summary(),
            visible_chat_summary=self._build_chat_summary(),
            revealed_signals=self._revealed_signals.copy(),
            step_count=self._state.step_count,
            done=self._state.done,
            reward=reward,
            last_action=last_action,
            case_status="closed" if self._state.done else "investigating",
        )

    def _build_profile_summary(self) -> str:
        profile = self._case["profile"]
        summary = f"{profile['name']}, {profile['age']}, {profile['location']}. {profile['headline']}"
        if self._state.profile_reviewed:
            summary += " " + profile.get("details", "")
        return summary

    def _build_chat_summary(self) -> str:
        chat = self._case["chat_history"]
        if self._state.chat_reviewed:
            summary = " | ".join(chat)
        else:
            summary = " | ".join(chat[:2])
        return summary

    def _handle_investigation_action(self, action: str) -> float:
        if self._case is None:
            return 0.0

        if action == "review_profile":
            if self._state.profile_reviewed:
                return -1.2
            self._state = self._state.model_copy(update={"profile_reviewed": True})
            self._reveal_signals("profile")
            return 2.0

        if action == "review_chat":
            if self._state.chat_reviewed:
                return -1.2
            self._state = self._state.model_copy(update={"chat_reviewed": True})
            self._reveal_signals("chat")
            return 2.2

        if action == "check_identity_risk":
            if self._state.identity_risk_checked:
                return -1.0
            self._state = self._state.model_copy(update={"identity_risk_checked": True})
            self._reveal_signals("identity")
            return 1.4 if "impersonation" in self._state.risk_types else 0.6

        if action == "check_financial_risk":
            if self._state.financial_risk_checked:
                return -1.0
            self._state = self._state.model_copy(update={"financial_risk_checked": True})
            self._reveal_signals("financial")
            return 2.3 if "financial_scam" in self._state.risk_types else 0.4

        if action == "check_offplatform_risk":
            if self._state.offplatform_risk_checked:
                return -1.0
            self._state = self._state.model_copy(update={"offplatform_risk_checked": True})
            self._reveal_signals("offplatform")
            return 2.0 if "offplatform_lure" in self._state.risk_types else 0.5

        if action == "request_human_review":
            if self._state.human_review_requested:
                return -1.0
            self._state = self._state.model_copy(update={"human_review_requested": True})
            if self._case["difficulty"] == "hard" or "low_confidence" in self._state.risk_types:
                self._reveal_signals("profile")
                self._reveal_signals("chat")
                return 1.2
            return -1.0

        return 0.0

    def _handle_final_decision(self, action: str) -> float:
        correct = action == self._state.ideal_resolution
        if correct:
            return 10.0

        if action == "flag_suspicious" and self._state.ground_truth in {"spam", "suspicious"}:
            return 5.0
        if action == "mark_legit" and self._state.ground_truth == "legit":
            return 8.0
        if action == "ban_user" and self._state.ground_truth == "spam":
            return 9.0

        return -10.0
