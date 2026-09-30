"""运行层：Runner 驱动一次子任务；模型只回文本时续上对话追问，并从各轮结果统计开销。"""

from __future__ import annotations

from agents import RunConfig, Runner
from utils.data import Case
from utils.env import DeliveryEnv
from utils.record import RunRecord

from .agent import agent, build_model
from .deps import DeliveryContext
from .output import Decision

# 模型偶尔查完直接回文本、不调 final_answer（SDK 把文本当作正常结束），用多轮对话追问兜底
MAX_REMINDERS = 2
REMINDER = {'role': 'user', 'content': '请调用 final_answer 工具提交最终下单决策，不要直接输出文本。'}


def solve(case: Case) -> RunRecord:
    context = DeliveryContext(case, DeliveryEnv(case))
    turn_input, runs, decision, error = case.instruction, [], None, ''
    try:
        for _ in range(MAX_REMINDERS + 1):
            result = Runner.run_sync(agent, turn_input, context=context, max_turns=20, run_config=RunConfig(model=build_model()))
            runs.append(result)
            # 停在 final_answer 时 final_output 是它返回的 JSON；只输出文本就结束时是那段文本
            if any(i.type == 'tool_call_item' and i.raw_item.name == 'final_answer' for i in result.new_items):
                decision = Decision.model_validate_json(result.final_output).model_dump()
                break
            # to_input_list() 是本轮完整对话（含工具调用与结果），追加提醒后接着跑，相当于多轮对话的下一轮
            turn_input = [*result.to_input_list(), REMINDER]
        else:
            error = f'提醒 {MAX_REMINDERS} 次后仍未调用 final_answer'
    except Exception as e:  # noqa: BLE001 — 单个子任务失败记为未命中；SDK 异常的 run_data 里仍有已发生的调用
        runs.append(getattr(e, 'run_data', None))
        error = f'{type(e).__name__}: {e}'
    runs = [r for r in runs if r is not None]
    responses = [resp for r in runs for resp in r.raw_responses]
    return RunRecord(
        decision=decision,
        error=error,
        llm_calls=len(responses),
        input_tokens=sum(resp.usage.input_tokens for resp in responses),
        output_tokens=sum(resp.usage.output_tokens for resp in responses),
        tool_calls=[i.raw_item.name for r in runs for i in r.new_items if i.type == 'tool_call_item' and i.raw_item.name != 'final_answer'],
    )
