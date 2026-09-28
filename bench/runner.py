"""评测：对一批 Case 逐个调用框架的 solve，判分、打印、写明细。命令行入口见根目录 run.py。

判分：选中的商品覆盖全部 target_product_ids 记为命中（hit），与目标集合完全一致记为精确（exact），
召回（recall）= 选中的目标商品占比，给多件商品的子任务部分分（其余选项可能同样合理，只是不在标准答案里）。
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from bench.data import Case
from bench.record import RunRecord

RESULT_DIR = Path(__file__).resolve().parents[1] / 'results'


def run(framework: str, solve: Callable[[Case], RunRecord], cases: list[tuple[Case, list[str]]]) -> None:
    RESULT_DIR.mkdir(exist_ok=True)
    out = RESULT_DIR / f'{framework}-{datetime.now():%Y%m%d-%H%M%S}.jsonl'
    rows = []
    for case, target in cases:
        start = time.perf_counter()
        record = solve(case)
        chosen = record.decision['product_ids'] if record.decision else []
        row = {
            'subtask_id': case.subtask_id,
            'skill_tested': case.skill_tested,
            'instruction': case.instruction,
            'target': target,
            'hit': set(target) <= set(chosen) and bool(chosen),
            'exact': set(target) == set(chosen),
            'recall': round(len(set(target) & set(chosen)) / len(target), 2),
            'seconds': round(time.perf_counter() - start, 1),
            **asdict(record),
        }
        rows.append(row)
        with out.open('a', encoding='utf-8') as f:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')
        print(
            f'[{"✓" if row["hit"] else "✗"}] {case.subtask_id} {case.instruction[:24]}… | 选 {chosen} 目标 {target} | '
            f'LLM {record.llm_calls} 次 工具 {len(record.tool_calls)} 次 {row["seconds"]}s {record.error[:80]}'
        )
    _summary(framework, rows, out)


def _summary(framework: str, rows: list[dict], out: Path) -> None:
    n = len(rows) or 1
    print(f'\n[{framework}] {len(rows)} 个子任务')
    print(f'  命中率 {sum(r["hit"] for r in rows) / n:.1%}  精确率 {sum(r["exact"] for r in rows) / n:.1%}  召回 {sum(r["recall"] for r in rows) / n:.1%}  出错 {sum(bool(r["error"]) for r in rows)} 个')
    print(
        f'  平均 LLM 调用 {sum(r["llm_calls"] for r in rows) / n:.1f} 次  工具 {sum(len(r["tool_calls"]) for r in rows) / n:.1f} 次  '
        f'输入 {sum(r["input_tokens"] for r in rows) / n:,.0f} tokens  输出 {sum(r["output_tokens"] for r in rows) / n:,.0f} tokens  '
        f'耗时 {sum(r["seconds"] for r in rows) / n:.1f}s'
    )
    print(f'  明细：{out}')

