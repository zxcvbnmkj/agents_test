"""唯一入口：加载一次子任务，依次交给各框架的 solve 评测。

    pdm run python run.py pydantic                          # 第一个用户的全部外卖子任务
    pdm run python run.py pydantic openai_agents langgraph --limit 3
    pdm run python run.py langgraph --users A891207 U901652 --history-chars 80000
"""

from __future__ import annotations

import argparse
import importlib

import config  # noqa: F401 — 先加载 .env 与直连网关设置，再导入各框架
from utils.data import load_cases
from utils.runner import run

# 按需导入：只跑其中一个框架时，不加载其余框架的库
FRAMEWORKS = {'pydantic': 'fw_pydantic', 'openai_agents': 'fw_openai_agents', 'langgraph': 'fw_langgraph'}


def main() -> None:
    parser = argparse.ArgumentParser(description='VitaBench-2 外卖子任务评测')
    parser.add_argument('frameworks', nargs='+', choices=FRAMEWORKS, help='要评测的框架，可多选，依次运行')
    parser.add_argument('--users', nargs='*', help='用户 id，缺省取第一个用户')
    parser.add_argument('--limit', type=int, default=None, help='最多跑几个子任务')
    parser.add_argument('--history-chars', type=int, default=60000, help='历史交互保留的最大字符数（从尾部保留）')
    parser.add_argument('--include-proactive', action='store_true', help='包含考察主动追问的子任务（单轮模式下无法追问，默认跳过）')
    args = parser.parse_args()

    cases = load_cases(args.users, args.history_chars, args.include_proactive)[: args.limit]
    for name in args.frameworks:
        run(name, importlib.import_module(f'{FRAMEWORKS[name]}.solve').solve, cases)


if __name__ == '__main__':
    main()
