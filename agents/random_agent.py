import random
import requests

BASE_URL = "http://127.0.0.1:8000"

ACTIONS = [
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


def main() -> None:
    response = requests.post(f"{BASE_URL}/reset")
    response.raise_for_status()
    observation = response.json()
    print("RESET OBSERVATION")
    print(observation)

    while True:
        action = random.choice(ACTIONS)
        print(f"\nTaking action: {action}")

        response = requests.post(
            f"{BASE_URL}/step",
            json={
                "action": {"action": action},
                "timeout_s": 30,
            },
        )
        response.raise_for_status()
        observation = response.json()
        print(observation)

        if observation["done"]:
            print("Episode finished")
            break


if __name__ == "__main__":
    main()