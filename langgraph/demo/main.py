"""
pdm run python langgraph/demo/main.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# 复用根目录 config.py（模型名/base_url/api_key 都在那里）。
# append 而非 insert(0)：避免根目录遮蔽真正的 langgraph 库。
sys.path.append(str(Path(__file__).resolve().parents[2]))
import config  # noqa: E402

from langchain.agents import create_agent  # noqa: E402
from langchain.agents.structured_output import ToolStrategy  # noqa: E402
from langchain_core.tools import tool  # noqa: E402
from langchain_openai import ChatOpenAI  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402


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


# ============ 2. 商家数据（demo 内置，真实场景可换成外部查询）============
STORE_NAMES = ['福记煲仔饭', '湘辣坊']


# ============ 3. 提示词 ============
SYSTEM_PROMPT = '你是外卖推荐助手。请先用 search_stores 查可选商家，需要商品详情时用 get_product，最后给出推荐。'


# ============ 4. 工具模块 ============
@tool
def search_stores(keyword: str | None = None) -> list[str]:
    """按关键词搜索商家。"""
    return [s for s in STORE_NAMES if keyword is None or keyword in s]


@tool
def get_product(product_id: str) -> dict:
    """获取商品详情。"""
    return {'product_id': product_id, 'name': f'商品{product_id}', 'price': 22.0}


def build_model() -> ChatOpenAI:
    """连真实 OneAPI 端点。"""
    return ChatOpenAI(model=config.MODEL_NAME, base_url=config.BASE_URL, api_key=config.API_KEY)


def main() -> None:
    # ToolStrategy 用工具调用产出结构化输出（该网关不支持原生 json_schema strict）。
    agent = create_agent(
        model=build_model(),
        tools=[search_stores, get_product],
        system_prompt=SYSTEM_PROMPT,
        response_format=ToolStrategy(RecommendationOutput),
    )

    result = agent.invoke({'messages': [('user', '推荐一家煲仔饭店')]})

    print('[结构化输出]')
    print(result['structured_response'].model_dump_json(indent=2))

    messages = result['messages']
    input_tokens = sum(m.usage_metadata['input_tokens'] for m in messages if getattr(m, 'usage_metadata', None))
    output_tokens = sum(m.usage_metadata['output_tokens'] for m in messages if getattr(m, 'usage_metadata', None))
    print(f'\n[用量] 输入 tokens={input_tokens} 输出 tokens={output_tokens}')


if __name__ == '__main__':
    main()
