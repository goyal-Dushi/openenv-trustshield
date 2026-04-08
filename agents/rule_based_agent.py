import requests

BASE_URL = "http://127.0.0.1:8000"


def choose_action(observation: dict) -> str:
    profile = observation["visible_profile_summary"].lower()
    chat = observation["visible_chat_summary"].lower()
    signals = " ".join(observation["revealed_signals"]).lower()

    last_action = observation.get("last_action")
    step_count = observation["step_count"]

    # Step 1: gather profile info first
    if "photos are generic" not in profile and last_action != "review_profile":
        return "review_profile"

    # Step 2: gather chat info
    if len(chat.split("|")) <= 2 and last_action != "review_chat":
        return "review_chat"

    # Risk checks based on evidence
    if any(term in signals for term in ["telegram", "whatsapp", "outside the app", "phone"]):
        return "check_offplatform_risk"

    if any(term in signals for term in ["money", "upi", "bank", "payment", "investment", "crypto"]):
        return "check_financial_risk"

    if any(term in signals for term in ["fake", "identity", "uncle", "impersonation"]):
        return "check_identity_risk"

    # Final decision
    if any(term in signals for term in ["telegram", "upi", "investment", "payment", "bank fraud"]):
        return "ban_user"

    if any(term in signals for term in ["suspicious", "off-platform", "unclear"]):
        return "flag_suspicious"

    if step_count >= 5:
        return "request_human_review"

    return "mark_legit"


def main() -> None:
    response = requests.post(f"{BASE_URL}/reset")
    response.raise_for_status()
    reset_result = response.json()

    print("RESET RESPONSE")
    print(reset_result)

    observation = reset_result["observation"]

    while True:
        print("\nCURRENT OBSERVATION")
        print(observation)

        action = choose_action(observation)
        print(f"\nChosen action: {action}")

        response = requests.post(
            f"{BASE_URL}/step",
            json={"action": {"action": action}, "timeout_s": 30},
        )
        response.raise_for_status()

        result = response.json()

        print("\nSTEP RESULT")
        print(result)

        observation = result["observation"]

        if result["done"]:
            print("\nEpisode finished")
            break


if __name__ == "__main__":
    main()