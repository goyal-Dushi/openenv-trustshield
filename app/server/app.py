from fastapi import FastAPI
from app.server.environment import TrustShieldEnvironment
from app.models import TrustShieldAction

app = FastAPI(title="TrustShield v1")

_env = TrustShieldEnvironment()

@app.get("/")
def root():
    return {
        "name": "TrustShield v1",
        "status": "ok",
        "message": "OpenEnv Trust & Safety benchmark is running."
    }


@app.post("/reset")
def reset():
    result = _env.reset()
    if hasattr(result, "model_dump"):
        return result.model_dump()
    return result


@app.post("/step")
def step(action: TrustShieldAction):
    result = _env.step(action)
    if hasattr(result, "model_dump"):
        return result.model_dump()
    return result


@app.get("/state")
def get_state():
    state = _env.get_state()
    if hasattr(state, "model_dump"):
        return state.model_dump()
    if isinstance(state, dict):
        return state
    return vars(state)