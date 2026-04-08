from openenv.core.env_server import create_web_interface_app

from app.models import TrustShieldAction, TrustShieldObservation
from app.server.environment import TrustShieldEnvironment

_env_instance = TrustShieldEnvironment()


def get_env_instance() -> TrustShieldEnvironment:
    return _env_instance


app = create_web_interface_app(
    get_env_instance,
    action_cls=TrustShieldAction,
    observation_cls=TrustShieldObservation,
)
