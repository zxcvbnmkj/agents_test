from bench.data import Case
from bench.env import DeliveryEnv

@dataclass
class Context:
    case: Case
    env: DeliveryEnv