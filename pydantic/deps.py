"""### 依赖注入

Pydantic AI 用 `RunContext[T]` 做依赖注入：Agent 构造时声明
`deps_type=T`，运行时把 `T` 的实例传给 `run_sync(deps=...)`，
工具、系统提示词、输出校验器通过 `ctx.deps` 拿到它。

这里把「当前任务 + 轮次 + 只读数据访问层」打包成一个 `TaskContext`，
作为唯一的依赖类型注入给智能体。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from schemas.models import (
    Environment,
    Product,
    Store,
    Subtask,
    Task,
    UserContext,
    UserProfile,
    Weather,
)


@dataclass
class TaskContext:
    """注入给 Agent 的运行时依赖。

    - `task` / `subtask`：当前任务与轮次（只含允许看到的字段）；
    - `repo`：封装对 `subtask.environment` 的只读查询，工具都通过它取数。
    """

    task_id: str
    subtask_id: str
    task: Task
    subtask: Subtask
    repo: DeliveryRepository


class DeliveryRepository:
    """只读数据访问层：把「从嵌套 JSON 里查数据」的细节收起来。

    工具模块只面向 `ctx.deps.repo` 编程，不直接碰字典，
    这样数据源将来换成 API/数据库时，工具层不用改。
    """

    def __init__(self, environment: Environment | None) -> None:
        self._env = environment or Environment()

    @property
    def current_time(self) -> str | None:
        return self._env.time

    def weather(self, date: str | None = None) -> list[Weather]:
        """按日期（YYYY-MM-DD）过滤天气；缺省返回全部天气记录。"""
        if date is None:
            return self._env.weather
        return [w for w in self._env.weather if w.datetime and w.datetime.startswith(date)]

    def delivery_addresses(self) -> list[str]:
        """当前环境中的可用配送地址。"""
        return [loc.address for loc in self._env.location if loc.address]

    def stores(
        self,
        *,
        keyword: str | None = None,
        min_score: float | None = None,
        store_type: str | None = None,
    ) -> list[Store]:
        """按名称关键词 / 最低评分 / 商家类型过滤商家。"""
        result: list[Store] = []
        for store in self._env.stores.values():
            if keyword and keyword not in (store.name or ""):
                continue
            if min_score is not None and (store.score or 0.0) < min_score:
                continue
            if store_type and store.store_type != store_type:
                continue
            result.append(store)
        return result

    def store(self, store_id: str) -> Store | None:
        """按 store_id 取商家详情（含全部商品）。"""
        return self._env.stores.get(store_id)

    def products(
        self,
        *,
        keyword: str | None = None,
        tags: list[str] | None = None,
        product_type: str | None = None,
        limit: int = 50,
    ) -> list[Product]:
        """跨商家搜索商品：名称关键词 / 标签（全含）/ 商品类型。"""
        result: list[Product] = []
        for store in self._env.stores.values():
            for product in store.products:
                if keyword and keyword not in (product.name or ""):
                    continue
                if tags and not set(tags).issubset(set(product.tags)):
                    continue
                if product_type and product.product_type != product_type:
                    continue
                result.append(product)
                if len(result) >= limit:
                    return result
        return result

    def product(self, product_id: str) -> Product | None:
        """按 product_id 取商品详情。"""
        for store in self._env.stores.values():
            for product in store.products:
                if product.product_id == product_id:
                    return product
        return None


# ---------------------------------------------------------------------------
# 任务装载与上下文构建
# ---------------------------------------------------------------------------


def load_task_file(path: str | Path) -> list[Task]:
    """读取 VitaBench-2 的 tasks.json / sample.json，解析为 Task 列表。"""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return [Task.model_validate(item) for item in raw]


def pick_task(tasks: list[Task], task_id: str | None = None) -> Task:
    """按 id 选任务；未指定时取第一个（sample.json 只有一个任务）。"""
    if task_id is None:
        return tasks[0]
    for task in tasks:
        if task.id == task_id:
            return task
    raise ValueError(f"未找到 task_id={task_id!r}，可选：{[t.id for t in tasks]}")


def build_context(task: Task, turn: int = 0) -> TaskContext:
    """把某个任务的第 turn 个 sub-task 装配成可注入的 TaskContext。"""
    subtask = task.subtasks[turn]
    return TaskContext(
        task_id=task.id or "",
        subtask_id=subtask.task_turn_num or f"turn-{turn}",
        task=task,
        subtask=subtask,
        repo=DeliveryRepository(subtask.environment),
    )


def _flatten_preferences(user_scenario: dict[str, Any] | None) -> list[str]:
    """把 user_scenario 里的偏好记忆摊平成可读字符串列表。

    例如 `{"饮食偏好": ["不爱吃蔬菜", "喜欢吃煲仔饭"]}` 会被摊平成
    `["饮食偏好: 不爱吃蔬菜、喜欢吃煲仔饭"]`。
    """
    if not user_scenario:
        return []
    memory = user_scenario.get("personalized_preference_memory") or {}
    current = memory.get("current") or {}
    lines: list[str] = []
    for key, value in current.items():
        if isinstance(value, list) and value:
            lines.append(f"{key}: {'、'.join(str(item) for item in value)}")
        elif value:
            lines.append(f"{key}: {value}")
    return lines


def build_user_context(task: Task, subtask: Subtask) -> UserContext:
    """聚合用户画像 + 偏好记忆 + 配送地址 + 当前时间，供工具返回。"""
    profile = task.user_profile or UserProfile()
    addresses = [loc.address for loc in subtask.environment.location if loc.address] if subtask.environment else []
    return UserContext(
        user_id=profile.user_id or task.id or "",
        occupation=profile.occupation,
        birth_date=profile.birth_date,
        residence=profile.residence,
        health_notes=profile.health_notes,
        preferences=_flatten_preferences(subtask.user_scenario),
        delivery_address=addresses[0] if addresses else None,
        current_time=subtask.environment.time if subtask.environment else None,
    )
