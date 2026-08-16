"""### 数据模型：VitaBench-2 任务 JSON 的强类型映射

把 131MB 的 tasks.json / sample.json 解析成类型安全的 Pydantic 模型，
避免在工具函数里到处写裸字典。

设计要点：
- `extra="ignore"`：JSON 里存在大量用不到的字段（例如环境里还有
  trains/hotels/flights 等其他场景数据），一律忽略，保持上下文精简。
- 隐藏答案字段（`target_product_ids`、`rubric`、`evaluation_criteria`）
  刻意**不建模**：它们属于评测金标准，不能进入智能体的上下文。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserProfile(BaseModel):
    """用户画像：来自 task 顶层的 user_profile 字段。

    JSON 里的键是中文（如「长期疾病/过敏史」），因此用 alias 映射到
    英文属性名；`populate_by_name=True` 让两种名字都能用于初始化。
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    occupation: str | None = Field(default=None, alias="职业")
    gender: str | None = Field(default=None, alias="性别")
    birth_date: str | None = Field(default=None, alias="出生日期")
    residence: str | None = Field(default=None, alias="常住地")
    work_address: str | None = Field(default=None, alias="工作地址")
    home_address: str | None = Field(default=None, alias="常住住址")
    hometown: str | None = Field(default=None, alias="籍贯")
    education: str | None = Field(default=None, alias="学历")
    family: list[str] = Field(default_factory=list, alias="家庭情况")
    #: 数据集里有时是字符串（"过敏性鼻炎"），有时是列表（["多囊卵巢综合征"]）
    health_notes: list[str] = Field(default_factory=list, alias="长期疾病/过敏史")
    user_id: str | None = None

    @field_validator("health_notes", mode="before")
    @classmethod
    def _health_notes_to_list(cls, value: Any) -> Any:
        """把 health_notes 统一成 list[str]，简化下游处理。"""
        if value is None:
            return []
        return [value] if isinstance(value, str) else value


class Weather(BaseModel):
    """某城市某天的天气信息。"""

    model_config = ConfigDict(extra="ignore")

    city: str | None = None
    category: str | None = None  # 晴 / 多云 / 小雨 ...
    datetime: str | None = None  # "2026-03-02"
    temperature: list[float] = Field(default_factory=list)  # [最低温, 最高温]
    humidity: float | None = None


class Location(BaseModel):
    """配送 / 商家坐标。"""

    model_config = ConfigDict(extra="ignore")

    address: str | None = None
    longitude: float | None = None
    latitude: float | None = None


class Product(BaseModel):
    """商家在售商品。

    `product_type`：normal / distraction（干扰项）/ irrelevant（无关项）。
    `distraction_reason` 会说明为什么该商品是干扰项。
    """

    model_config = ConfigDict(extra="ignore")

    name: str | None = None
    price: float | None = None
    tags: list[str] = Field(default_factory=list)  # 辣度、份量、菜系等标签
    attributes: list[str] = Field(default_factory=list)  # 配料明细
    product_type: str | None = None
    quantity: int | None = None  # 库存
    product_id: str | None = None
    store_id: str | None = None
    store_name: str | None = None
    distraction_reason: str | None = None


class Store(BaseModel):
    """外卖商家，`products` 为该店全部在售商品。"""

    model_config = ConfigDict(extra="ignore")

    name: str | None = None
    score: float | None = None
    location: Location | None = None
    tags: list[str] = Field(default_factory=list)  # 菜系、配送时长、营业时间等
    store_type: str | None = None  # normal / distraction
    products: list[Product] = Field(default_factory=list)
    store_id: str | None = None
    distraction_reason: str | None = None


class Environment(BaseModel):
    """某个 sub-task 的实时环境：时间、天气、地点、商家/商品库。"""

    model_config = ConfigDict(extra="ignore")

    time: str | None = None  # "2026-03-02 11:35:00"
    weather: list[Weather] = Field(default_factory=list)
    location: list[Location] = Field(default_factory=list)
    stores: dict[str, Store] = Field(default_factory=dict)
    user_id: str | None = None


class Subtask(BaseModel):
    """一个 sub-task = 一轮用户请求 + 对应环境。

    只保留智能体**允许看到**的字段；`target_product_ids`、`rubric`、
    `evaluation_criteria` 等隐藏金标准被 `extra="ignore"` 过滤掉。
    """

    model_config = ConfigDict(extra="ignore")

    task_turn_num: str | None = None  # 例如 "U901652_01"
    domain: str | None = None  # delivery / instore / ota ...
    instruction: str | None = None  # 用户本轮的真实请求
    task: str | None = None  # 任务类型，例如 "外卖-晚餐"
    environment: Environment | None = None
    #: 更丰富的画像/偏好记忆（保留原始 dict，便于扩展使用）
    user_scenario: dict[str, Any] | None = None


class Task(BaseModel):
    """VitaBench-2 中的一个完整任务（一个用户、多个 sub-task）。"""

    model_config = ConfigDict(extra="ignore")

    id: str | None = None
    user_id: str | None = None
    user_profile: UserProfile | None = None
    subtasks: list[Subtask] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 工具返回用的“摘要”模型：字段比完整模型少，给模型的上下文更精简
# ---------------------------------------------------------------------------


class StoreBrief(BaseModel):
    """商家摘要（列表展示用）。"""

    store_id: str
    name: str
    score: float | None = None
    tags: list[str] = Field(default_factory=list)
    store_type: str | None = None


class ProductBrief(BaseModel):
    """商品摘要（列表展示用）。"""

    product_id: str
    name: str
    price: float | None = None
    tags: list[str] = Field(default_factory=list)
    product_type: str | None = None
    store_id: str | None = None
    store_name: str | None = None


class UserContext(BaseModel):
    """聚合后的用户上下文，供 `get_user_context` 工具返回给模型。"""

    user_id: str
    occupation: str | None = None
    birth_date: str | None = None
    residence: str | None = None
    health_notes: list[str] = Field(default_factory=list)
    preferences: list[str] = Field(default_factory=list)  # 偏好记忆摘要
    delivery_address: str | None = None
    current_time: str | None = None
