"""模型看到的最终输出：Decision 的类说明与 Field description 进入 schema，final_answer 的名字与描述只在这里定义。

Decision 在三个框架里各有一份，内容必须一致，否则对比不公平。
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from pydantic_ai import ToolOutput


class Decision(BaseModel):
    store_id: str = Field(description='下单商家的 store_id，必须来自工具返回')
    product_ids: list[str] = Field(description='下单商品的 product_id，须属于该商家；用户要几样就列几样')
    delivery_address: str = Field(description='送达地址，从用户常用地址中选')
    reason: str = Field(description='一句话说明选择理由，对应用户的指令与偏好')


FINAL_ANSWER = ToolOutput(Decision, name='final_answer', description='提交最终下单决策，调用即结束任务；必须通过本工具交付，不要直接输出文本')
