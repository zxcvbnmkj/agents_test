"""### 组装层：把各模块装配成唯一的 Agent

按项目规则（只能有一个 agent），本模块只创建并返回一个 Agent 实例。
入口层（main.py）负责把真实模型或测试模型传进来。
"""

from __future__ import annotations

from pydantic_ai import Agent
from pydantic_ai.tools import RunContext

from capabilities.delivery import delivery_capability
from deps import TaskContext
from prompts import load_system_prompt
from schemas.output import RecommendationOutput
from tools.delivery import get_user_context, get_weather


def build_agent(model) -> Agent[TaskContext, RecommendationOutput]:
    """构建并返回唯一的外卖推荐 Agent。

    参数 `model`：Pydantic AI 的 Model 实例（真实模型或 TestModel），
    这样「装配」与「选模型」解耦，方便测试和后续接评测 harness。

    装配内容：
    - `output_type`：结构化输出（schemas/output.py），模型必须按此返回；
    - `deps_type`：依赖注入类型（deps.py 的 TaskContext）；
    - `system_prompt`：基础系统提示词（prompts/system.md）；
    - `tools`：常驻工具（用户上下文、天气）；
    - `capabilities`：按需加载的能力（商家/商品库查询）。
    """
    agent = Agent(
        model=model,
        name="vita-bench-2-delivery-agent",
        output_type=RecommendationOutput,
        deps_type=TaskContext,
        system_prompt=load_system_prompt(),
        tools=[get_user_context, get_weather],
        capabilities=[delivery_capability],
    )

    @agent.system_prompt
    def _dynamic_context(ctx: RunContext[TaskContext]) -> str:
        """动态系统提示词：每次 run 时把当前轮次信息注入给模型。"""
        return (
            f"当前轮次：{ctx.deps.subtask_id}；"
            f"任务类型：{ctx.deps.subtask.task or '未知'}；"
            f"当前时间：{ctx.deps.repo.current_time or '未知'}"
        )

    return agent
