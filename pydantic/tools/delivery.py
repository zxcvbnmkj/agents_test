"""### 工具模块：外卖场景只读查询工具

工具都是**只读**的：只从依赖注入的 `DeliveryRepository` 查询数据，
不产生任何副作用，也不读取评测金标准。
"""

from __future__ import annotations

from pydantic_ai.tools import RunContext

from deps import TaskContext, build_user_context
from schemas.models import Product, ProductBrief, Store, StoreBrief, UserContext, Weather


def get_user_context(ctx: RunContext[TaskContext]) -> UserContext:
    """获取用户画像、饮食偏好、配送地址与当前时间，用于定制外卖推荐。"""
    return build_user_context(ctx.deps.task, ctx.deps.subtask)


def get_weather(ctx: RunContext[TaskContext], date: str | None = None) -> list[Weather]:
    """查询天气信息；date 为 YYYY-MM-DD，缺省返回环境中的天气列表。"""
    return ctx.deps.repo.weather(date)


def search_stores(
    ctx: RunContext[TaskContext],
    keyword: str | None = None,
    min_score: float | None = None,
    limit: int = 10,
) -> list[StoreBrief]:
    """按名称关键词与最低评分搜索商家，返回商家摘要（评分、标签、类型）。"""
    stores = ctx.deps.repo.stores(keyword=keyword, min_score=min_score)
    return [
        StoreBrief(
            store_id=store.store_id or "",
            name=store.name or "",
            score=store.score,
            tags=store.tags,
            store_type=store.store_type,
        )
        for store in stores[:limit]
    ]


def get_store(ctx: RunContext[TaskContext], store_id: str) -> Store | None:
    """按 store_id 获取商家详情，含该店全部在售商品。"""
    return ctx.deps.repo.store(store_id)


def search_products(
    ctx: RunContext[TaskContext],
    keyword: str | None = None,
    tags: list[str] | None = None,
    limit: int = 20,
) -> list[ProductBrief]:
    """按名称关键词与标签搜索商品，返回商品摘要（价格、标签、所属商家）。"""
    products = ctx.deps.repo.products(keyword=keyword, tags=tags)
    return [
        ProductBrief(
            product_id=product.product_id or "",
            name=product.name or "",
            price=product.price,
            tags=product.tags,
            product_type=product.product_type,
            store_id=product.store_id,
            store_name=product.store_name,
        )
        for product in products[:limit]
    ]


def get_product(ctx: RunContext[TaskContext], product_id: str) -> Product | None:
    """按 product_id 获取商品详情（含配料 attributes 与干扰项标记）。"""
    return ctx.deps.repo.product(product_id)
