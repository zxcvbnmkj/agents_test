"""### 能力模块

能力（Capability）是 Pydantic AI 的可复用行为单元：指令 + 工具 + 设置的打包。
`defer_loading=True` 的能力会折叠成一行目录，模型需要时才通过
`load_capability` 工具按需加载，从而精简每轮上下文。
"""
