"""本地上下文：运行时传 Runner.run_sync(context=...)，工具与动态 instructions 经 RunContextWrapper.context 读取，不会发给模型。"""

from __future__ import annotations

from dataclasses import dataclass

from utils.data import Case
from utils.env import DeliveryEnv


@dataclass
class DeliveryContext:
    case: Case
    env: DeliveryEnv
