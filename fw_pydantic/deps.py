"""依赖注入：一次子任务运行的上下文。instructions 用 case 渲染系统提示词，工具经 ctx.deps.env 查商家库。"""

from __future__ import annotations

from dataclasses import dataclass

from utils.data import Case
from utils.env import DeliveryEnv


@dataclass
class Deps:
    case: Case
    env: DeliveryEnv
