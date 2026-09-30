"""外卖商家库的只读查询逻辑，与框架无关。

各框架按自己的风格把这三个方法包装成工具（pydantic-ai 的 RunContext 工具、Agents SDK 的 @function_tool、
LangChain 的 @tool），工具 docstring 一律照抄这里，保证所有框架给模型看的工具说明一字不差。
"""

from __future__ import annotations

from utils.data import Case


class DeliveryEnv:
    def __init__(self, case: Case):
        self._stores = case.stores
        self._history = case.history
        self._history_search = case.history_search

    def search_user_history(self, keywords: list[str], limit: int = 20) -> str:
        """根据具体关键词查询用户行为记录；匹配会参考行为和对话，但返回仅含行为。
        关键词优先使用商品名、品牌名、店铺名、行为类型及同义词，不要使用抽象概念；结果不相关时可换关键词重试。"""
        terms = {keyword for keyword in keywords if keyword}
        blocks = [block.strip() for block in self._history.split('\n## ') if block.strip()]
        blocks = [block if block.startswith('## ') else f'## {block}' for block in blocks]
        search_blocks = [block.strip() for block in self._history_search.split('\n## ') if block.strip()]
        search_blocks = [block if block.startswith('## ') else f'## {block}' for block in search_blocks]
        matched = [block for block, searchable in zip(blocks, search_blocks) if not terms or any(term in searchable for term in terms)]
        return '\n\n'.join(matched[-limit:]) or '没有找到与当前请求相关的历史记录。'

    def search_stores(self, keywords: list[str] | None = None, limit: int = 10) -> list[dict]:
        """搜索外卖商家：按关键词命中数量排序，最多返回 limit 家。
        返回 store_id、店名、评分、标签（含菜系、配送时长、营业时间）。关键词应具体，不传关键词只返回前 limit 家。"""
        scored = []
        for sid, store in self._stores.items():
            fields = (store['name'], *store['tags'], *(p['name'] for p in store['products']))
            score = sum(any(_hit(keyword, field) for field in fields) for keyword in (keywords or []))
            if not keywords or score:
                scored.append((score, store['score'], sid, store))
        scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return [
            {'store_id': sid, 'name': store['name'], 'score': store['score'], 'tags': store['tags']}
            for _, _, sid, store in scored[:limit]
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
