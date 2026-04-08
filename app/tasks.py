import random
from typing import Any

CASES: list[dict[str, Any]] = [
    {
        "case_id": "case-001",
        "difficulty": "easy",
        "profile": {
            "name": "Ali Khan",
            "age": 29,
            "location": "Mumbai",
            "headline": "New to matrimony app, looking for serious match.",
            "details": "Joined 2 days ago and only a few profile photos are visible."
        },
        "chat_history": [
            "Hi, I saw your profile and I think we are a good match.",
            "I have a special investment opportunity for you.",
            "Send ₹15,000 to my Paytm account and I will transfer a larger amount back.",
            "We should move to WhatsApp so I can share the details."
        ],
        "signals": {
            "profile": [
                "Profile created very recently.",
                "Only two photos and limited personal details."
            ],
            "chat": [
                "Talks about urgent investment money.",
                "Asks to continue on WhatsApp outside the app."
            ],
            "identity": ["Claims to be a software engineer but profile details are vague."],
            "financial": ["Requests an upfront money transfer.", "Mentions a high-return investment."],
            "offplatform": ["Pushes the conversation to WhatsApp."]
        },
        "ground_truth": "spam",
        "ideal_resolution": "ban_user",
        "risk_types": ["financial_scam", "offplatform_lure"]
    },
    {
        "case_id": "case-002",
        "difficulty": "easy",
        "profile": {
            "name": "Neha Sharma",
            "age": 25,
            "location": "Delhi",
            "headline": "Looking for life partner and serious discussion.",
            "details": "Photos are generic, and the profile is only 1 week old."
        },
        "chat_history": [
            "Hello beautiful, you have a lovely smile.",
            "My uncle works in the UK and wants to introduce you to a good match.",
            "Please verify your identity on Telegram before we proceed.",
            "It is safer if we talk on Telegram, I will send a voice note."
        ],
        "signals": {
            "profile": [
                "New account with only generic profile information.",
                "Speaker claims a family introduction but offers no real detail."
            ],
            "chat": [
                "Asks to verify identity on Telegram.",
                "Uses exaggerated romantic language early in the conversation."
            ],
            "identity": ["No supporting details about family or work."],
            "financial": ["No direct money request yet, but uses off-platform pressure."],
            "offplatform": ["Encourages moving to Telegram outside the app."]
        },
        "ground_truth": "spam",
        "ideal_resolution": "ban_user",
        "risk_types": ["offplatform_lure", "impersonation"]
    },
    {
        "case_id": "case-003",
        "difficulty": "medium",
        "profile": {
            "name": "Rahul Mehta",
            "age": 31,
            "location": "Pune",
            "headline": "Single professional looking for honest partner.",
            "details": "Profile has a few strong photo shots but the bio is minimal."
        },
        "chat_history": [
            "Hi, you look like someone I can connect with.",
            "I feel we have a deep emotional bond already.",
            "Can we switch to WhatsApp? The app is too slow for me.",
            "I have to leave the country soon; I need someone who understands me."
        ],
        "signals": {
            "profile": [
                "Bio is unusually short for a matchmaking profile.",
                "The user has only two photos and is new on the platform."
            ],
            "chat": [
                "Attempts emotional manipulation by claiming a strong bond.",
                "Pushes to move the conversation to WhatsApp quickly."
            ],
            "identity": ["Profile details are not consistent with a trusted match."],
            "financial": ["No explicit money ask, but off-platform contact is suspicious."],
            "offplatform": ["Requests to continue on WhatsApp outside the app."]
        },
        "ground_truth": "suspicious",
        "ideal_resolution": "flag_suspicious",
        "risk_types": ["offplatform_lure", "emotional_manipulation"]
    },
    {
        "case_id": "case-004",
        "difficulty": "medium",
        "profile": {
            "name": "Pooja Verma",
            "age": 28,
            "location": "Jaipur",
            "headline": "Seeking partner for serious marriage proposal.",
            "details": "Profile has some good details, but the job and education fields differ from chat claims."
        },
        "chat_history": [
            "Hello, I belong to a respected family and I want an honest life partner.",
            "Please send your phone number so I can ask my relatives to call you.",
            "I do not want to waste time on the app."
        ],
        "signals": {
            "profile": [
                "There are inconsistencies between profile details and the chat story.",
                "The account mentions a good family but provides no validation."
            ],
            "chat": [
                "Requests personal contact information too quickly.",
                "Claims to avoid app communication without clear reason."
            ],
            "identity": ["Claims and profile data do not fully align."],
            "financial": ["No direct request for money yet."],
            "offplatform": ["Asks to move conversation off-platform and share phone details."]
        },
        "ground_truth": "suspicious",
        "ideal_resolution": "flag_suspicious",
        "risk_types": ["impersonation", "low_confidence"]
    },
    {
        "case_id": "case-005",
        "difficulty": "hard",
        "profile": {
            "name": "Aman Gupta",
            "age": 33,
            "location": "Bengaluru",
            "headline": "Engineer and foodie looking for genuine relationship.",
            "details": "Well-written profile with real work details, but the first message is slightly scripted."
        },
        "chat_history": [
            "Hello, I enjoyed reading your profile and would like to know more.",
            "I work in software and love travel.",
            "Let us continue here before moving to the phone."
        ],
        "signals": {
            "profile": [
                "Profile appears complete and consistent.",
                "The user has several genuine details in the bio."
            ],
            "chat": [
                "The messages are polite and not pushy.",
                "There is no direct request to move off-platform or send money."
            ],
            "identity": ["The profile appears traceable and consistent."],
            "financial": ["No financial risk indicators are present."],
            "offplatform": ["The user explicitly wants to stay on the app for now."]
        },
        "ground_truth": "legit",
        "ideal_resolution": "mark_legit",
        "risk_types": ["low_confidence"]
    },
    {
        "case_id": "case-006",
        "difficulty": "hard",
        "profile": {
            "name": "Sanya Rao",
            "age": 27,
            "location": "Hyderabad",
            "headline": "Teacher looking for a partner who respects family values.",
            "details": "Profile is detailed and the messages are consistent, but there is a hint of a rehearsed introduction."
        },
        "chat_history": [
            "Hi, your profile looks wonderful and I appreciate your values.",
            "I would like to know more about your family and goals.",
            "I prefer to keep the conversation here until we know each other better."
        ],
        "signals": {
            "profile": [
                "Profile content is coherent and not overly generic.",
                "User shares a stable job and family background."
            ],
            "chat": [
                "The chat is warm but not manipulative.",
                "No asks for money or off-platform contact."
            ],
            "identity": ["Profile details are consistent across the case."],
            "financial": ["No financial red flags are present."],
            "offplatform": ["User chooses to stay on the app."]
        },
        "ground_truth": "legit",
        "ideal_resolution": "mark_legit",
        "risk_types": ["low_confidence"]
    }
]

TASKS: dict[str, str] = {
    "easy_spam_financial": "case-001",
    "easy_spam_impersonation": "case-002",
    "medium_suspicious_emotional": "case-003",
    "medium_suspicious_profile_mismatch": "case-004",
    "hard_legit_engineer": "case-005",
    "hard_legit_teacher": "case-006",
}


def get_all_cases() -> list[dict[str, Any]]:
    return CASES


def get_case_by_id(case_id: str) -> dict[str, Any]:
    for case in CASES:
        if case["case_id"] == case_id:
            return case
    raise ValueError(f"Unknown case_id: {case_id}")


def get_task_case(task_name: str) -> dict[str, Any]:
    if task_name not in TASKS:
        raise ValueError(f"Unknown task: {task_name}")
    return get_case_by_id(TASKS[task_name])


def list_tasks() -> list[str]:
    return list(TASKS.keys())


def get_random_case() -> dict[str, Any]:
    return random.choice(CASES)