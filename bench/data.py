"""数据加载：把 VitaBench-2 的外卖子任务转成 agent 可见的 Case，标准答案另行返回。

脱敏用白名单：store_type / product_type / distraction_reason 是干扰项标注，target_product_ids / rubric /
evaluation_criteria 是答案，user_scenario / historical_* 是真实偏好的标准答案——都不能进 agent 上下文。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

TASK_FILE = Path(__file__).resolve().parents[1] / 'VitaBench-2' / 'tasks.json'
_WEEKDAYS = '一二三四五六日'


@dataclass
class Case:
    user_id: str
    subtask_id: str
    skill_tested: list[str]
    instruction: str
    time: str
    profile: dict
    addresses: list[str]
    weather: list[dict]
    history: str
    stores: dict[str, dict]


def load_cases(user_ids: list[str] | None, history_chars: int, include_proactive: bool) -> list[tuple[Case, list[str]]]:
    """返回 [(Case, target_product_ids)]；user_ids 为空取第一个用户。"""
    tasks = json.loads(TASK_FILE.read_text(encoding='utf-8'))
    tasks = [t for t in tasks if t['id'] in user_ids] if user_ids else tasks[:1]
    cases = []
    for task in tasks:
        history: list[str] = []
        for sub in task['subtasks']:
            # 累积到当前子任务为止的全部历史（官方 Full Context 口径）
            history.extend(_render_interaction(i) for i in sub['interactions'])
            skills = [s for s in sub.get('skill_tested') or [] if s]
            if sub['domain'] != 'delivery' or not sub.get('target_product_ids'):
                continue
            if 'proactive' in skills and not include_proactive:
                continue
            env = sub['environment']
            case = Case(
                user_id=task['id'],
                subtask_id=sub['subtask_id'],
                skill_tested=skills,
                instruction=sub['instruction'],
                time=env['time'],
                profile=task['user_profile'],
                addresses=[loc['address'] for loc in env['location']],
                weather=env['weather'],
                history=_tail('\n'.join(history), history_chars),
                stores={sid: _visible_store(s) for sid, s in env['stores'].items()},
            )
            cases.append((case, sub['target_product_ids']))
    return cases


def weekday(time: str) -> str:
    return '星期' + _WEEKDAYS[datetime.strptime(time, '%Y-%m-%d %H:%M:%S').weekday()]


def _visible_store(store: dict) -> dict:
    return {
        'name': store['name'],
        'score': store['score'],
        'tags': store['tags'],
        'products': [
            {k: p[k] for k in ('product_id', 'name', 'price', 'tags', 'attributes', 'quantity')} for p in store['products']
        ],
    }


def _render_interaction(item: dict) -> str:
    lines = [f'## {item["date"]}']
    lines += [f'- 行为 {b["behavior_type"]}：{json.dumps(b["content"], ensure_ascii=False)}' for b in item.get('behavior') or []]
    lines += [f'{"用户" if d["role"] == "user" else "助手"}：{d["content"]}' for d in item.get('dialogue') or []]
    return '\n'.join(lines)


def _tail(text: str, max_chars: int) -> str:
    """超长时从头部截断，保留最近的记录，并对齐到行首。"""
    if len(text) <= max_chars:
        return text
    tail = text[-max_chars:]
    return tail[tail.find('\n') + 1 :]
