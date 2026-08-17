"""### 入口层 (main)

VitaBench-2 外卖推荐任务的 Pydantic AI 智能体入口。

运行方式（请用脚本方式运行）：

    pdm run python pydantic/main.py                          # 默认跑 sample.json 第一个任务
    pdm run python pydantic/main.py --task-file VitaBench-2/tasks.json --task-id A891207 --turn 0

离线自检（不调用真实模型、不产生费用）：

    pdm run python pydantic/main.py --dry-run

注意：不要用 `python -m pydantic.main` 运行——本地 `pydantic/` 目录
没有 `__init__.py`，脚本方式能保证 `import pydantic_ai` 引用到真正的
pydantic 库，而不会被本目录遮蔽。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 复用根目录 config.py。append 而非 insert(0)：避免根目录遮蔽真正的 pydantic 库。
sys.path.append(str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402
from agent import build_agent
from deps import build_context, load_task_file, pick_task

#: 默认任务文件：相对于本文件定位仓库根目录，避免依赖运行时 cwd
_DEFAULT_TASK_FILE = Path(__file__).resolve().parents[1] / "VitaBench-2" / "sample.json"

#: --dry-run 模式下 TestModel 返回的样例结构化输出
_DRY_RUN_OUTPUT = {
    "summary": "（离线自检样例）根据用户画像与约束，推荐排骨煲仔饭（大份、微辣、无蔬菜）。",
    "delivery_address": "四川省成都市大邑县兴隆佳苑33-1-2",
    "store_id": "S00001",
    "store_name": "示例商家",
    "order_items": [
        {"product_id": "P00001", "product_name": "排骨煲仔饭 大份", "price": 22.0, "quantity": 1},
    ],
    "reasons": ["大份", "微辣", "无蔬菜", "煲仔饭"],
    "avoided": ["含青菜心等蔬菜配菜的商品", "中份/小份商品"],
    "confidence": 0.9,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="VitaBench-2 外卖推荐任务 · Pydantic AI 智能体")
    parser.add_argument("--task-file", type=Path, default=_DEFAULT_TASK_FILE, help="tasks.json / sample.json 路径")
    parser.add_argument("--task-id", default=None, help="任务 id（缺省取文件中的第一个任务）")
    parser.add_argument("--turn", type=int, default=0, help="sub-task 轮次下标（缺省 0）")
    parser.add_argument("--dry-run", action="store_true", help="用 TestModel 离线自检，不调用真实模型")
    parser.add_argument("--model", default=config.MODEL_NAME, help="模型名称")
    parser.add_argument("--base-url", default=config.BASE_URL, help="OpenAI 兼容端点 base_url")
    parser.add_argument("--api-key", default=config.API_KEY, help="API Key")
    return parser.parse_args()


def _build_model(args: argparse.Namespace):
    """根据参数构造模型：dry-run 用 TestModel，否则用真实 OneAPI 端点。"""
    if args.dry_run:
        from pydantic_ai.models.test import TestModel

        # call_tools=[]：不调用任何工具，直接返回下面的结构化输出样例
        return TestModel(call_tools=[], custom_output_args=_DRY_RUN_OUTPUT, model_name="test")

    from pydantic_ai.models.openai import OpenAIModel
    from pydantic_ai.providers.openai import OpenAIProvider

    return OpenAIModel(
        args.model,
        provider=OpenAIProvider(base_url=args.base_url, api_key=args.api_key),
    )


def main() -> int:
    args = parse_args()

    tasks = load_task_file(args.task_file)
    task = pick_task(tasks, args.task_id)
    context = build_context(task, args.turn)
    print(f"[任务] {context.task_id} | 轮次 {context.subtask_id} | 指令：{context.subtask.instruction}")

    agent = build_agent(model=_build_model(args))
    result = agent.run_sync(context.subtask.instruction or "", deps=context)

    print("\n[结构化输出]")
    print(result.output.model_dump_json(indent=2, ensure_ascii=False))

    usage = result.usage  # 本版本中 usage 是属性（RunUsage），不是方法
    print(
        f"\n[用量] 输入 tokens={usage.input_tokens} "
        f"输出 tokens={usage.output_tokens} 请求次数={usage.requests}"
    )
    print(f"[轨迹] 消息数={len(result.all_messages())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
