"""### 提示词模块

把系统提示词从代码里抽出来放到 Markdown 文件，方便迭代和对比实验。
"""

from __future__ import annotations

from pathlib import Path

_SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent / "system.md"


def load_system_prompt() -> str:
    """读取系统提示词（角色 + 工作流程 + 注意事项）。"""
    return _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
