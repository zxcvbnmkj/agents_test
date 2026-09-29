"""LangGraph 版：把 ReAct 循环显式画成状态图。

    START → agent ─┬─ 调查询工具 → tools ──→ agent
                   ├─ 调 Decision → respond ─┬─ 参数合法 → END
                   │                         └─ 校验失败 → agent（带错误重试）
                   └─ 只输出文本 → remind ──→ agent

State 是图里流转的数据（消息 + 最终决策）；Context 是本次运行的只读依赖（case、商家库），
经 Runtime / ToolRuntime 注入节点和工具，不进 State、也不发给模型。
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import config
import tracing
from bench.prompt import prompt_vars
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.runtime import Runtime
from pydantic import ValidationError

from .deps import Context
from .output import Decision, State
from .tools import TOOLS

tracing.setup_langchain()

# Decision 作为「提交工具」一起绑定：模型调它即表示给出最终答案，由 respond 节点接住而不是 ToolNode 执行
llm = ChatOpenAI(
    model=config.MODEL_NAME,
    base_url=config.BASE_URL,
    api_key=config.API_KEY,
    temperature=config.TEMPERATURE,
    extra_body=config.EXTRA_BODY,
    timeout=120,
    max_retries=2,
).bind_tools([*TOOLS, Decision])

# 系统模板 + 对话历史占位，与模型用 | 串成一条链（LCEL）；系统提示词每轮现渲染、不写进 State
prompt = ChatPromptTemplate.from_messages(
    [('system', (Path(__file__).parent / 'system.md').read_text(encoding='utf-8')), MessagesPlaceholder('messages')]
)
chain = prompt | llm


def agent(state: State, runtime: Runtime[Context]) -> dict:
    return {'messages': [chain.invoke({**prompt_vars(runtime.context.case), 'messages': state['messages']})]}


def route_after_agent(state: State) -> Literal['tools', 'respond', 'remind']:
    calls = state['messages'][-1].tool_calls
    if any(c['name'] == Decision.__name__ for c in calls):
        return 'respond'
    return 'tools' if calls else 'remind'


def respond(state: State) -> dict:
    call = next(c for c in state['messages'][-1].tool_calls if c['name'] == Decision.__name__)
    try:
        return {'decision': Decision.model_validate(call['args'])}
    except ValidationError as e:
        return {'messages': [ToolMessage(f'参数校验失败，请修正后重新提交：{e}', tool_call_id=call['id'])]}


def route_after_respond(state: State) -> Literal['agent', '__end__']:
    return END if state.get('decision') else 'agent'


def remind(state: State) -> dict:
    return {'messages': [HumanMessage(f'请调用 {Decision.__name__} 工具提交最终下单决策，不要直接输出文本。')]}


builder = StateGraph(State, context_schema=Context)
builder.add_node('agent', agent)
builder.add_node('tools', ToolNode(TOOLS))
builder.add_node('respond', respond)
builder.add_node('remind', remind)
builder.add_edge(START, 'agent')
builder.add_conditional_edges('agent', route_after_agent)
builder.add_edge('tools', 'agent')
builder.add_conditional_edges('respond', route_after_respond)
builder.add_edge('remind', 'agent')
graph = builder.compile()
