"""工具层：第一个参数 RunContext[Deps] 由 pydantic-ai 注入、不进 schema；docstring 即模型看到的工具说明（照抄 bench/env.py）。"""

from __future__ import annotations

from pydantic_ai import RunContext

from .deps import Deps


def search_stores(ctx: RunContext[Deps], keywords: list[str] | None = None) -> list[dict]:
    """搜索外卖商家：店名、标签或在售商品名命中任一关键词即返回；不传关键词返回全部商家。
    返回 store_id、店名、评分、标签（含菜系、配送时长、营业时间）。"""
    return ctx.deps.env.search_stores(keywords)


def get_store_products(ctx: RunContext[Deps], store_id: str) -> list[dict] | dict:
    """查看某商家在售的全部商品：product_id、名称、价格、标签、配料、库存。"""
    return ctx.deps.env.get_store_products(store_id)


def search_products(ctx: RunContext[Deps], keywords: list[str]) -> list[dict]:
    """跨商家搜索商品：商品名、标签或配料命中任一关键词即返回，结果附带所属 store_id 与店名。"""
    return ctx.deps.env.search_products(keywords)
