from openenv import create_web_interface_app
from app.models import TrustShieldAction, TrustShieldObservation
from app.server.environment import TrustShieldEnvironment

def get_env_instance():
    return TrustShieldEnvironment()

app = create_web_interface_app(
    get_env_instance,
    action_cls=TrustShieldAction,
    observation_cls=TrustShieldObservation,
)