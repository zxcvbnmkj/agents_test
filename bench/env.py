"""外卖商家库的只读查询逻辑，与框架无关。

各框架按自己的风格把这三个方法包装成工具（pydantic-ai 的 RunContext 工具、Agents SDK 的 @function_tool、
LangChain 的 @tool），工具 docstring 一律照抄这里，保证所有框架给模型看的工具说明一字不差。
"""

from __future__ import annotations

from bench.data import Case


class DeliveryEnv:
    def __init__(self, case: Case):
        self._stores = case.stores

    def search_stores(self, keywords: list[str] | None = None) -> list[dict]:
        """搜索外卖商家：店名、标签或在售商品名命中任一关键词即返回；不传关键词返回全部商家。
        返回 store_id、店名、评分、标签（含菜系、配送时长、营业时间）。"""
        return [
            {'store_id': sid, 'name': s['name'], 'score': s['score'], 'tags': s['tags']}
            for sid, s in self._stores.items()
            if not keywords or any(_hit(k, s['name'], *s['tags'], *(p['name'] for p in s['products'])) for k in keywords)
        ]

    def get_store_products(self, store_id: str) -> list[dict] | dict:
        """查看某商家在售的全部商品：product_id、名称、价格、标签、配料、库存。"""
        store = self._stores.get(store_id)
        return store['products'] if store else {'error': f'商家 {store_id} 不存在'}

    def search_products(self, keywords: list[str]) -> list[dict]:
        """跨商家搜索商品：商品名、标签或配料命中任一关键词即返回，结果附带所属 store_id 与店名。"""
        return [
            {**p, 'store_id': sid, 'store_name': s['name']}
            for sid, s in self._stores.items()
            for p in s['products']
            if any(_hit(k, p['name'], *p['tags'], *p['attributes']) for k in keywords)
        ]


def _hit(keyword: str, *fields: str) -> bool:
    return any(keyword in f for f in fields)
