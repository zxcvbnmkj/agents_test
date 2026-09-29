from langgraph.graph import MessagesState
from pydantic import BaseModel, Field


class Decision(BaseModel):
    """最终下单决策：查询完成后提交，提交即结束任务。"""

    store_id: str = Field(description='下单商家的 store_id，必须来自工具返回')
    product_ids: list[str] = Field(description='下单商品的 product_id，须属于该商家；用户要几样就列几样')
    delivery_address: str = Field(description='送达地址，从用户常用地址中选')
    reason: str = Field(description='一句话说明选择理由，对应用户的指令与偏好')


class State(MessagesState):
    decision: Decision | None
