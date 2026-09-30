"""solve 交给评测的运行记录：框架与 utils 之间唯一的数据接口。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RunRecord:
    """一次子任务运行的结果与开销，由各框架填写，runner 负责计时与判分。

    decision 是各框架 Decision.model_dump() 的字典，至少含 product_ids；None 表示没交出决策。
    """

    decision: dict | None
    error: str = ''
    llm_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    tool_calls: list[str] = field(default_factory=list)
