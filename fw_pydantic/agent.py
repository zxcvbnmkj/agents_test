"""组装层：唯一的 Agent 与模型构建。模型不在此绑定，入口层 run 时以 model= 传入。"""

from __future__ import annotations

from pathlib import Path

import config
from bench.prompt import prompt_vars
from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from .deps import Deps
from .output import FINAL_ANSWER
from .tools import get_store_products, search_products, search_stores

SYSTEM_PROMPT = (Path(__file__).parent / 'system.md').read_text(encoding='utf-8')
MODEL_SETTINGS = {'temperature': config.TEMPERATURE, 'extra_body': config.EXTRA_BODY}


def build_model() -> OpenAIChatModel:
    """每次现建客户端：AsyncOpenAI 会绑定首个事件循环，跨 run_sync 复用会读到已关闭的 socket。"""
    client = AsyncOpenAI(base_url=config.BASE_URL, api_key=config.API_KEY, timeout=120.0, max_retries=2)
    _downgrade_required_tool_choice(client)
    return OpenAIChatModel(config.MODEL_NAME, provider=OpenAIProvider(openai_client=client))


def _downgrade_required_tool_choice(client: AsyncOpenAI) -> None:
    """豆包网关对 tool_choice='required' 高频返回不带 tool_call 的空响应，auto 下模型照样按描述调 final_answer。
    pydantic-ai 因输出走 ToolOutput 强制 required、无法用 model_settings 覆盖，故在客户端出口降级。"""
    completions = client.chat.completions
    original_create = completions.create

    async def create(*args, **kwargs):
        if kwargs.get('tool_choice') == 'required':
            kwargs['tool_choice'] = 'auto'
        return await original_create(*args, **kwargs)

    completions.create = create


def _instructions(ctx: RunContext[Deps]) -> str:
    return SYSTEM_PROMPT.format(**prompt_vars(ctx.deps.case))


agent = Agent(
    deps_type=Deps,
    output_type=FINAL_ANSWER,
    retries=3,
    instructions=_instructions,
    tools=[search_stores, get_store_products, search_products],
)
