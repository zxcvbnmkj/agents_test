"""模型看到的最终输出：Decision 与 final_answer 工具。

不用 Agent 的 output_type：它走 response_format 的 JSON Schema 约束，豆包网关会忽略，模型照样输出自然语言导致解析失败；
改为普通工具 final_answer，配合 agent.py 里的 StopAtTools「调到它就结束」。
Decision 在三个框架里各有一份，内容必须一致，否则对比不公平。
"""

from __future__ import annotations

from agents import FunctionTool
from agents.strict_schema import ensure_strict_json_schema
from agents.tool_context import ToolContext
from pydantic import BaseModel, Field

from .deps import DeliveryContext


class Decision(BaseModel):
    """最终下单决策：查询完成后提交，提交即结束任务。"""

    store_id: str = Field(description='下单商家的 store_id，必须来自工具返回')
    product_ids: list[str] = Field(description='下单商品的 product_id，须属于该商家；用户要几样就列几样')
    delivery_address: str = Field(description='送达地址，从用户常用地址中选')
    reason: str = Field(description='一句话说明选择理由，对应用户的指令与偏好')


async def _submit(ctx: ToolContext[DeliveryContext], args: str) -> str:
    # StopAtTools 会把工具返回值转成字符串作为 final_output，这里就返回校验过的 JSON，solve 再解析回 Decision
    return Decision.model_validate_json(args).model_dump_json()


# 手写 FunctionTool 而非 @function_tool(decision: Decision)：后者会把参数包成 {"decision": {...}} 的嵌套 schema，
# 这里直接以 Decision 的扁平字段作参数，与 pydantic-ai / LangGraph 给模型的形状一致，对比才公平
final_answer = FunctionTool(
    name='final_answer',
    description='提交最终下单决策，调用即结束任务；必须通过本工具交付，不要直接输出文本。',
    params_json_schema=ensure_strict_json_schema(Decision.model_json_schema()),
    on_invoke_tool=_submit,
)
