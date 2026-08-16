"""### 结构化输出模块

`RecommendationOutput` 会作为 Agent 的 `output_type`：
Pydantic AI 会把它的 JSON Schema 注册成输出工具，强制模型按此结构返回，
再对返回结果做校验（不合法会自动让模型重试）。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class OrderItem(BaseModel):
    """推荐下单的单个商品。"""

    product_id: str
    product_name: str
    price: float
    quantity: int = 1


class RecommendationOutput(BaseModel):
    """外卖推荐的结构化结果。

    字段说明：
    - `summary`：给用户的自然语言推荐说明；
    - `reasons`：每条理由应尽量对齐用户画像里的约束（如大份/微辣/无蔬菜/煲仔饭）；
    - `avoided`：明确排除的干扰项及其原因，便于评测时做归因。
    """

    summary: str = Field(description="给用户的推荐说明")
    delivery_address: str = Field(description="本次下单的配送地址")
    store_id: str = Field(description="推荐商家的 store_id")
    store_name: str = Field(description="推荐商家名称")
    order_items: list[OrderItem] = Field(description="推荐下单的商品清单")
    reasons: list[str] = Field(default_factory=list, description="推荐理由，逐条对应约束")
    avoided: list[str] = Field(default_factory=list, description="排除的干扰项及原因")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="推荐置信度（0~1）")
