"""运行层：以 stream 方式跑一遍状态图，并从最后一个 State 统计开销。"""

from __future__ import annotations

from bench.data import Case
from bench.env import DeliveryEnv
from bench.record import RunRecord
from langchain_core.messages import AIMessage

from .graph import Context, Decision, graph

# 每次模型调用对应 agent + 后继节点两步，与其他框架「最多 20 次模型调用」对齐
RECURSION_LIMIT = 2 * 20 + 1


def solve(case: Case) -> RunRecord:
    # stream_mode='values' 每步产出完整 State：中途超限抛错时，仍能拿最后一个 State 统计开销
    state = {'messages': []}
    try:
        for state in graph.stream(
            {'messages': [('user', case.instruction)], 'decision': None},
            context=Context(case, DeliveryEnv(case)),
            config={'recursion_limit': RECURSION_LIMIT},
            stream_mode='values',
        ):
            pass
        record = RunRecord(decision=state['decision'].model_dump())
    except Exception as e:  # noqa: BLE001 — 单个子任务失败记为未命中，不中断整轮评测
        record = RunRecord(decision=None, error=f'{type(e).__name__}: {e}')
    replies = [m for m in state['messages'] if isinstance(m, AIMessage)]
    record.llm_calls = len(replies)
    record.input_tokens = sum((m.usage_metadata or {}).get('input_tokens', 0) for m in replies)
    record.output_tokens = sum((m.usage_metadata or {}).get('output_tokens', 0) for m in replies)
    record.tool_calls = [c['name'] for m in replies for c in m.tool_calls if c['name'] != Decision.__name__]
    return record
