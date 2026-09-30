from langchain.tools import ToolRuntime, tool

from .deps import Context


@tool
def search_stores(runtime: ToolRuntime[Context], keywords: list[str] | None = None, limit: int = 10) -> list[dict]:
    """搜索外卖商家：按关键词命中数量排序，最多返回 limit 家；不传关键词也只返回前 limit 家。"""
    return runtime.context.env.search_stores(keywords, limit)


@tool
def get_store_products(runtime: ToolRuntime[Context], store_id: str) -> list[dict] | dict:
    """查看某商家在售的全部商品：product_id、名称、价格、标签、配料、库存。"""
    return runtime.context.env.get_store_products(store_id)


@tool
def search_products(runtime: ToolRuntime[Context], keywords: list[str]) -> list[dict]:
    """跨商家搜索商品：商品名、标签或配料命中任一关键词即返回，结果附带所属 store_id 与店名。"""
    return runtime.context.env.search_products(keywords)


@tool
def search_user_history(runtime: ToolRuntime[Context], keywords: list[str], limit: int = 20) -> str:
    """根据具体关键词查询用户行为记录；匹配会参考行为和对话，但返回仅含行为。
    关键词优先使用商品名、品牌名、店铺名、行为类型及同义词，不要使用抽象概念；结果不相关时可换关键词重试。"""
    return runtime.context.env.search_user_history(keywords, limit)


TOOLS = [search_stores, get_store_products, search_products, search_user_history]
