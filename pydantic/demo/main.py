"""
pdm run python pydantic/demo/main.py

覆盖 Pydantic AI 全流程：提示词 → 依赖注入 → 工具 → 能力模块
(defer_loading=True) → 结构化输出 → 运行。


    pdm run python pydantic/demo/main.py
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

# 复用父目录 pydantic/config.py（模型名/base_url/api_key 都在那里）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402

from pydantic import BaseModel, Field  # noqa: E402
from pydantic_ai import Agent  # noqa: E402
from pydantic_ai.capabilities import Capability  # noqa: E402
from pydantic_ai.tools import RunContext  # noqa: E402


# ============ 1. 结构化输出模块 ============
class OrderItem(BaseModel):
    product_id: str
    product_name: str
    price: float


class RecommendationOutput(BaseModel):
    """最终结构化输出：模型必须按这个结构返回。"""

    summary: str
    store_name: str
    order_items: list[OrderItem]
    reasons: list[str] = Field(default_factory=list)


# ============ 2. 依赖注入 ============
@dataclass
class Deps:
    """运行时依赖：通过 ctx.deps 注入给工具和提示词。"""

    user_name: str
    store_names: list[str]


# ============ 3. 提示词 ============
SYSTEM_PROMPT = '你是外卖推荐助手。请先用 search_stores 查可选商家，需要商品详情时用 get_product，最后按结构化格式给出推荐。'


# ============ 4. 工具模块 ============
def search_stores(ctx: RunContext[Deps], keyword: str | None = None) -> list[str]:
    """按关键词搜索商家。"""
    return [s for s in ctx.deps.store_names if keyword is None or keyword in s]


def get_product(ctx: RunContext[Deps], product_id: str) -> dict:
    """获取商品详情。"""
    return {'product_id': product_id, 'name': f'商品{product_id}', 'price': 22.0}


# ============ 5. 能力模块（defer_loading=True 按需延迟加载）============
# 能力里的工具平时不进上下文，模型需要时通过 load_capability 按需加载。
demo_capability = Capability(
    id='demo-delivery',
    description='外卖推荐能力：需要查商品详情时加载，提供 get_product 工具',
    tools=[get_product],
    defer_loading=True,
)


def build_model():
    """连真实 OneAPI 端点。"""
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider

    return OpenAIChatModel(config.MODEL_NAME, provider=OpenAIProvider(base_url=config.BASE_URL, api_key=config.API_KEY))


def main() -> None:
    agent = Agent(
        model=build_model(),
        output_type=RecommendationOutput,
        deps_type=Deps,
        system_prompt=SYSTEM_PROMPT,
        tools=[search_stores],
        capabilities=[demo_capability],
    )

    result = agent.run_sync(
        '推荐一家煲仔饭店',
        deps=Deps(user_name='小明', store_names=['福记煲仔饭', '湘辣坊']),
    )

    print('[结构化输出]')
    print(result.output.model_dump_json(indent=2, ensure_ascii=False))

    usage = result.usage
    print(f'\n[用量] 输入 tokens={usage.input_tokens} 输出 tokens={usage.output_tokens} 请求次数={usage.requests}')


if __name__ == '__main__':
    main()
