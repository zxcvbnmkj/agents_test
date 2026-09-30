"""运行层：跑一次子任务，并从消息记录里统计开销。"""

from __future__ import annotations

from utils.data import Case
from utils.env import DeliveryEnv
from utils.record import RunRecord
from pydantic_ai import capture_run_messages
from pydantic_ai.messages import ModelResponse, ToolCallPart
from pydantic_ai.usage import UsageLimits

from .agent import MODEL_SETTINGS, agent, build_model
from .deps import Deps


def solve(case: Case) -> RunRecord:
    with capture_run_messages() as messages:
        try:
            result = agent.run_sync(
                case.instruction,
                deps=Deps(case, DeliveryEnv(case)),
                model=build_model(),
                model_settings=MODEL_SETTINGS,
                usage_limits=UsageLimits(request_limit=20),
            )
            record = RunRecord(decision=result.output.model_dump())
        except Exception as e:  # noqa: BLE001 — 单个子任务失败记为未命中，不中断整轮评测
            record = RunRecord(decision=None, error=f'{type(e).__name__}: {e}')
    responses = [m for m in messages if isinstance(m, ModelResponse)]
    record.llm_calls = len(responses)
    record.input_tokens = sum(m.usage.input_tokens for m in responses)
    record.output_tokens = sum(m.usage.output_tokens for m in responses)
    record.tool_calls = [p.tool_name for m in responses for p in m.parts if isinstance(p, ToolCallPart) and p.tool_name != 'final_answer']
    return record
