from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import traceback

from app.server.environment import TrustShieldEnvironment

app = FastAPI(title="TrustShield")

_env: Optional[TrustShieldEnvironment] = None

class ResetRequest(BaseModel):
    task_name: Optional[str] = None


class StepRequest(BaseModel):
    action: str

@app.get("/")
def root():
    return {
        "name": "TrustShield",
        "status": "ok",
        "message": "OpenEnv Trust & Safety benchmark is running.",
    }


@app.post("/reset")
def reset(task_name: Optional[str] = None):
    global _env
    try:
        _env = TrustShieldEnvironment(seed=42)
        result = _env.reset(task_name=task_name)
        
        return result.model_dump()
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/step")
def step(req: StepRequest):
    global _env

    if _env is None:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")

    try:
        result = _env.step(req.action)

        return result.model_dump()

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/state")
def get_state():
    global _env

    if _env is None:
        raise HTTPException(status_code=400, detail="Environment not initialized.")

    try:
        return _env.state.model_dump()

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))