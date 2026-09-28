"""依赖注入：一次子任务运行的上下文。instructions 用 case 渲染系统提示词，工具经 ctx.deps.env 查商家库。"""

from __future__ import annotations

from dataclasses import dataclass

from bench.data import Case
from bench.env import DeliveryEnv


@dataclass
class Deps:
    case: Case
    env: DeliveryEnv
