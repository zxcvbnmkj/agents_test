"""工具层：@function_tool 由 docstring 与类型注解生成工具说明和参数 schema（照抄 bench/env.py）；
第一个参数 RunContextWrapper 由 SDK 注入、不进 schema。
"""

from __future__ import annotations

import json

from agents import RunContextWrapper, function_tool

from .deps import DeliveryContext


# SDK 把非字符串返回值直接 str() 成 Python repr，工具统一返回 JSON 字符串，与其他框架给模型的内容一致
def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False)


@function_tool
def search_stores(ctx: RunContextWrapper[DeliveryContext], keywords: list[str] | None = None) -> str:
    """搜索外卖商家：店名、标签或在售商品名命中任一关键词即返回；不传关键词返回全部商家。
    返回 store_id、店名、评分、标签（含菜系、配送时长、营业时间）。"""
    return _json(ctx.context.env.search_stores(keywords))


@function_tool
def get_store_products(ctx: RunContextWrapper[DeliveryContext], store_id: str) -> str:
    """查看某商家在售的全部商品：product_id、名称、价格、标签、配料、库存。"""
    return _json(ctx.context.env.get_store_products(store_id))


@function_tool
def search_products(ctx: RunContextWrapper[DeliveryContext], keywords: list[str]) -> str:
    """跨商家搜索商品：商品名、标签或配料命中任一关键词即返回，结果附带所属 store_id 与店名。"""
    return _json(ctx.context.env.search_products(keywords))
