from dataclasses import dataclass

from utils.data import Case
from utils.env import DeliveryEnv


@dataclass
class Context:
    case: Case
    env: DeliveryEnv
