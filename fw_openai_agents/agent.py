"""装配层：Agent 是一份声明式配置（instructions / tools / tool_use_behavior / model_settings），
循环由 Runner 驱动：模型调工具 → SDK 执行并回填 → 直到模型调用 final_answer，其返回值即最终结果。
模型不在此绑定，solve.py 运行时以 run_config=RunConfig(model=...) 传入。
"""

from __future__ import annotations

from pathlib import Path

import config
from agents import Agent, ModelSettings, OpenAIChatCompletionsModel, RunContextWrapper, StopAtTools, set_tracing_disabled
from utils.prompt import prompt_vars
from openai import AsyncOpenAI

from .deps import DeliveryContext
from .output import final_answer
from .tools import get_store_products, search_products, search_stores, search_user_history

SYSTEM_PROMPT = (Path(__file__).parent.parent / 'utils' / 'system.md').read_text(encoding='utf-8')

# 当前项目使用自定义 OpenAI 兼容网关，且没有 OpenAI Traces 的认证配置。
# 禁用 SDK 默认的 OpenAI tracing，避免每次运行产生 401；模型调用不受影响。
set_tracing_disabled(True)

def build_model() -> OpenAIChatCompletionsModel:
    """网关只兼容 Chat Completions，不用 SDK 默认的 Responses API；每次现建客户端，避免跨事件循环复用。"""
    client = AsyncOpenAI(base_url=config.BASE_URL, api_key=config.API_KEY, timeout=120.0, max_retries=2)
    return OpenAIChatCompletionsModel(model=config.MODEL_NAME, openai_client=client)


def dynamic_instructions(ctx: RunContextWrapper[DeliveryContext], agent: Agent[DeliveryContext]) -> str:
    """instructions 可以是函数：每次调模型前现算，拿到本次运行的上下文。"""
    return SYSTEM_PROMPT.format(**prompt_vars(ctx.context.case))


agent = Agent[DeliveryContext](
    name='外卖下单助手',
    instructions=dynamic_instructions,
    tools=[search_stores, get_store_products, search_products, search_user_history, final_answer],
    tool_use_behavior=StopAtTools(stop_at_tool_names=['final_answer']),
    model_settings=ModelSettings(temperature=config.TEMPERATURE, extra_body=config.EXTRA_BODY),
)
