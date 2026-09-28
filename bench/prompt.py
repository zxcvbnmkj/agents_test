"""把一个子任务整理成系统提示词模板的变量。

模板 system.md 放在各框架目录内（各自加载、注入），三份内容必须保持一致，否则对比不公平。
用户指令不进模板，作为用户消息单独发送。
"""

from __future__ import annotations

import json

from bench.data import Case, weekday


def prompt_vars(case: Case) -> dict[str, str]:
    return {
        'time': f'{case.time} {weekday(case.time)}',
        'weather': json.dumps(case.weather, ensure_ascii=False),
        'addresses': '；'.join(case.addresses),
        'profile': json.dumps(case.profile, ensure_ascii=False),
        'history': case.history,
    }
