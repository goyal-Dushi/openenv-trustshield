from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.models import TrustShieldAction
from app.server.environment import TrustShieldEnvironment

app = FastAPI(
    title="TrustShield v1",
    description="OpenEnv-based Trust & Safety investigation benchmark.",
    version="0.1.0",
)

env = TrustShieldEnvironment()


@app.get("/")
def home():
    return RedirectResponse(url="/docs")


@app.post("/reset")
def reset():
    return env.reset().model_dump()


@app.post("/step")
def step(action: TrustShieldAction):
    return env.step(action).model_dump()


@app.get("/state")
def get_state():
    return env.get_state()