"""### 工具模块

把智能体需要的外部能力封装成带类型的工具函数。
每个工具的第一个参数都是 `RunContext[TaskContext]`，Pydantic AI 会自动
注入 `ctx.deps`；函数 docstring 会被提取为模型可见的工具说明。
"""
