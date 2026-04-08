from __future__ import annotations

from typing import Any

from pydantic import BaseModel, field_validator

ALLOWED_ACTIONS = {
    "review_profile",
    "review_chat",
    "check_identity_risk",
    "check_financial_risk",
    "check_offplatform_risk",
    "request_human_review",
    "mark_legit",
    "flag_suspicious",
    "ban_user",
}


class TrustShieldAction(BaseModel):
    action: str

    model_config = {"extra": "forbid"}

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: str) -> str:
        if value not in ALLOWED_ACTIONS:
            raise ValueError(f"Invalid action: {value}")
        return value


class TrustShieldObservation(BaseModel):
    case_id: str
    visible_profile_summary: str
    visible_chat_summary: str
    revealed_signals: list[str]
    step_count: int
    done: bool
    reward: float
    last_action: str | None
    case_status: str

    model_config = {"extra": "forbid"}


class TrustShieldState(BaseModel):
    episode_id: str
    case_id: str
    ground_truth: str
    ideal_resolution: str
    difficulty: str
    risk_types: list[str]
    step_count: int
    done: bool

    profile_reviewed: bool
    chat_reviewed: bool
    identity_risk_checked: bool
    financial_risk_checked: bool
    offplatform_risk_checked: bool
    human_review_requested: bool

    profile: dict[str, Any]
    chat_history: list[str]
    signals: dict[str, list[str]]

    model_config = {"extra": "forbid"}
