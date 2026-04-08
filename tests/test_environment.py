from app.models import TrustShieldAction
from app.server.environment import TrustShieldEnvironment


def test_reset_returns_observation():
    env = TrustShieldEnvironment(seed=0)
    observation = env.reset()

    assert observation.case_id
    assert not observation.done
    assert observation.step_count == 0
    assert isinstance(observation.visible_profile_summary, str)
    assert isinstance(observation.visible_chat_summary, str)
    assert isinstance(observation.revealed_signals, list)


def test_review_profile_changes_observation():
    env = TrustShieldEnvironment(seed=1)
    env.reset()

    observation = env.step(TrustShieldAction(action="review_profile"))

    assert observation.step_count == 1
    assert observation.reward > -0.5
    assert not observation.done
    assert "profile" in observation.last_action


def test_review_chat_changes_observation():
    env = TrustShieldEnvironment(seed=1)
    env.reset()

    observation = env.step(TrustShieldAction(action="review_chat"))

    assert observation.step_count == 1
    assert observation.reward > -0.5
    assert not observation.done
    assert observation.last_action == "review_chat"


def test_final_action_ends_episode():
    env = TrustShieldEnvironment(seed=2)
    env.reset()

    observation = env.step(TrustShieldAction(action="mark_legit"))

    assert observation.done
    assert isinstance(observation.reward, float)
    assert observation.case_status == "closed"


def test_repeated_review_profile_is_penalized():
    env = TrustShieldEnvironment(seed=3)
    env.reset()

    first_observation = env.step(TrustShieldAction(action="review_profile"))
    second_observation = env.step(TrustShieldAction(action="review_profile"))

    assert second_observation.reward < first_observation.reward


def test_environment_state_updates_after_actions():
    env = TrustShieldEnvironment(seed=4)
    env.reset()

    env.step(TrustShieldAction(action="review_profile"))
    env.step(TrustShieldAction(action="review_chat"))

    state = env.state

    assert state.profile_reviewed is True
    assert state.chat_reviewed is True
    assert state.step_count == 2
    assert state.done is False


def test_done_environment_should_not_allow_more_steps():
    env = TrustShieldEnvironment(seed=5)
    env.reset()

    env.step(TrustShieldAction(action="mark_legit"))

    try:
        env.step(TrustShieldAction(action="review_profile"))
        assert False, "Expected ValueError when stepping after episode is done"
    except ValueError as exc:
        assert "Episode already finished" in str(exc)


def test_reset_after_done_starts_fresh_episode():
    env = TrustShieldEnvironment(seed=6)
    env.reset()

    env.step(TrustShieldAction(action="mark_legit"))
    new_observation = env.reset()

    assert new_observation.step_count == 0
    assert new_observation.done is False
    assert new_observation.case_status == "investigating"


def test_invalid_action_should_fail_validation():
    try:
        TrustShieldAction(action="hack_the_system")
        assert False, "Expected validation failure for invalid action"
    except Exception as exc:
        assert "Invalid action" in str(exc)