from fastapi import FastAPI, HTTPException
from app.server.environment import TrustShieldEnvironment
from app.models import TrustShieldAction
import traceback

app = FastAPI(title="TrustShield")

_env = TrustShieldEnvironment()

@app.get("/")
def root():
    return {
        "name": "TrustShield",
        "status": "ok",
        "message": "OpenEnv Trust & Safety benchmark is running."
    }

@app.post("/reset")
def reset():
    try:
        result = _env.reset()
        if hasattr(result, "model_dump"):
            return result.model_dump()
        return result
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/step")
def step(action: TrustShieldAction):
    try:
        result = _env.step(action)
        if hasattr(result, "model_dump"):
            return result.model_dump()
        return result
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/state")
def get_state():
    try:
        state = _env.get_state()
        if hasattr(state, "model_dump"):
            return state.model_dump()
        if isinstance(state, dict):
            return state
        return vars(state)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))