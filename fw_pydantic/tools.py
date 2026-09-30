from __future__ import annotations

from pydantic_ai import RunContext

from .deps import Deps


def search_stores(ctx: RunContext[Deps], keywords: list[str] | None = None, limit: int = 10) -> list[dict]:
    """搜索外卖商家：按关键词命中数量排序，关键词列表的元素必须是单个词语。最多返回 limit 家；不传关键词也只返回前 limit 家。"""
    return ctx.deps.env.search_stores(keywords, limit)


def get_store_products(ctx: RunContext[Deps], store_id: str) -> list[dict] | dict:
    """查看某商家在售的全部商品：product_id、名称、价格、标签、配料、库存。"""
    return ctx.deps.env.get_store_products(store_id)


def search_products(ctx: RunContext[Deps], keywords: list[str]) -> list[dict]:
    """跨商家搜索商品：商品名、标签或配料命中任一关键词即返回，结果附带所属 store_id 与店名。"""
    return ctx.deps.env.search_products(keywords)


def search_user_history(ctx: RunContext[Deps], keywords: list[str], limit: int = 20) -> str:
    """根据具体关键词查询用户行为记录；匹配会参考行为和对话，但返回仅含行为。
    关键词优先使用商品名、品牌名、店铺名、行为类型及同义词，不要使用抽象概念；结果不相关时可换关键词重试。"""
    return ctx.deps.env.search_user_history(keywords, limit)
