"""### 能力模块：外卖推荐能力（defer_loading=True 按需延迟加载）

把「商家/商品库查询」工具与外卖推荐业务指令打包成一个按需加载的能力：
- 模型第一轮只看到一行目录描述，不用背 4 个工具的 schema；
- 一旦需要查库，模型调用 `load_capability`，工具和指令才进入上下文；
- 同一轮 run 内加载过一次后保持可用，不需要重复加载。
"""

from __future__ import annotations

from pydantic_ai.capabilities import Capability

from tools.delivery import get_product, get_store, search_products, search_stores

#: 能力的稳定 id：defer_loading=True 时必须有，历史回放依赖它
DELIVERY_CAPABILITY_ID = "vita-delivery-recommendation"

DELIVERY_INSTRUCTIONS = """\
你正在处理「外卖推荐」任务。加载本能力后，你可以查询商家与商品：
- search_stores：按关键词/最低评分筛选商家；
- get_store：查看商家详情（含全部商品）；
- search_products：按关键词/标签筛选商品；
- get_product：查看商品详情（含配料与干扰项标记）。

推荐时必须遵守：
1. 优先满足用户画像中的健康/过敏/忌口约束（例如多囊卵巢综合征、
   过敏性鼻炎等），并结合偏好记忆中的份量、辣度、菜系、忌口蔬菜；
2. 结合当前时间、天气与配送地址判断合理性（如深夜不推早餐类商家）；
3. store_type / product_type 为 distraction 的商家/商品通常是干扰项，
   不要作为首选；如确无更优选择，必须在 summary 里说明原因；
4. 下单前确认商品有库存（quantity > 0）且与商家匹配；
5. 最终结论交给结构化输出（RecommendationOutput），不要输出隐藏答案。
"""

#: 按需加载的外卖推荐能力：id 稳定，description 作为目录条目展示给模型
delivery_capability = Capability(
    id=DELIVERY_CAPABILITY_ID,
    description=(
        "外卖推荐：需要查询商家/商品库时加载本能力，"
        "加载后提供 search_stores、get_store、search_products、get_product 工具与外卖推荐规则。"
    ),
    instructions=DELIVERY_INSTRUCTIONS,
    tools=[search_stores, get_store, search_products, get_product],
    defer_loading=True,
)
