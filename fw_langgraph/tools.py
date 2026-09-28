@tool
def search_stores(runtime: ToolRuntime[Context], keywords: list[str] | None = None) -> list[dict]:
    """搜索外卖商家：店名、标签或在售商品名命中任一关键词即返回；不传关键词返回全部商家。
    返回 store_id、店名、评分、标签（含菜系、配送时长、营业时间）。"""
    return runtime.context.env.search_stores(keywords)


@tool
def get_store_products(runtime: ToolRuntime[Context], store_id: str) -> list[dict] | dict:
    """查看某商家在售的全部商品：product_id、名称、价格、标签、配料、库存。"""
    return runtime.context.env.get_store_products(store_id)


@tool
def search_products(runtime: ToolRuntime[Context], keywords: list[str]) -> list[dict]:
    """跨商家搜索商品：商品名、标签或配料命中任一关键词即返回，结果附带所属 store_id 与店名。"""
    return runtime.context.env.search_products(keywords)


TOOLS = [search_stores, get_store_products, search_products]
