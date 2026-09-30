"""评测：对一批 Case 逐个调用框架的 solve，判分、打印、写明细。命令行入口见根目录 run.py。

判分：商品和店铺分别计算命中（hit）、精确（exact）与召回（recall）。
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from utils.data import Case
from utils.record import RunRecord

RESULT_DIR = Path(__file__).resolve().parents[1] / 'results'


def run(framework: str, solve: Callable[[Case], RunRecord], cases: list[tuple[Case, list[str]]]) -> None:
    RESULT_DIR.mkdir(exist_ok=True)
    out = RESULT_DIR / f'{framework}-{datetime.now():%Y%m%d-%H%M%S}.jsonl'
    rows = []
    for case, target in cases:
        start = time.perf_counter()
        record = solve(case)
        chosen = record.decision['product_ids'] if record.decision else []
        chosen_stores = {record.decision['store_id']} if record.decision and record.decision.get('store_id') else set()
        target_stores = {
            sid for sid, store in case.stores.items()
            if any(product['product_id'] in target for product in store['products'])
        }
        row = {
            'subtask_id': case.subtask_id,
            'skill_tested': case.skill_tested,
            'instruction': case.instruction,
            'target': target,
            'hit': set(target) <= set(chosen) and bool(chosen),
            'exact': set(target) == set(chosen),
            'recall': round(len(set(target) & set(chosen)) / len(target), 2),
            'target_stores': sorted(target_stores),
            'chosen_stores': sorted(chosen_stores),
            'store_hit': bool(chosen_stores) and target_stores <= chosen_stores,
            'store_exact': target_stores == chosen_stores,
            'store_recall': round(len(target_stores & chosen_stores) / len(target_stores), 2) if target_stores else 0.0,
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
    print(f'  商品  命中率 {sum(r["hit"] for r in rows) / n:.1%}  精确率 {sum(r["exact"] for r in rows) / n:.1%}  召回 {sum(r["recall"] for r in rows) / n:.1%}')
    print(f'  店铺  命中率 {sum(r["store_hit"] for r in rows) / n:.1%}  精确率 {sum(r["store_exact"] for r in rows) / n:.1%}  召回 {sum(r["store_recall"] for r in rows) / n:.1%}  出错 {sum(bool(r["error"]) for r in rows)} 个')
    print(
        f'  平均 LLM 调用 {sum(r["llm_calls"] for r in rows) / n:.1f} 次  工具 {sum(len(r["tool_calls"]) for r in rows) / n:.1f} 次  '
        f'输入 {sum(r["input_tokens"] for r in rows) / n:,.0f} tokens  输出 {sum(r["output_tokens"] for r in rows) / n:,.0f} tokens  '
        f'耗时 {sum(r["seconds"] for r in rows) / n:.1f}s'
    )
    print(f'  明细：{out}')
