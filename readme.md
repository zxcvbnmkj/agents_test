# 工作流与智能体效果评估

用同一份数据、同一套工具、同一个提示词、同一个模型，对比不同 agent 框架的写法与效果。

## 基准数据集

### VitaBench 2.0 是什么

[VitaBench 2.0](https://github.com/meituan-longcat/VitaBench-2.0)（[论文](https://arxiv.org/abs/2605.27141) · [数据](https://huggingface.co/datasets/meituan-longcat/VitaBench-2.0)）是美团 LongCat 团队发布的生活服务类 agent 基准，考察**长期交互中的个性化与主动性**：agent 要从跨越数月的零散对话和行为日志里**推断**用户偏好、在模糊指令下**运用**偏好，并在偏好变化时**更新**认知。1.0 考的是「能否完成一个复杂请求」，2.0 进一步问「能否从日常交互中理解这个用户」。

本地数据在 `VitaBench-2/tasks.json`（131MB）：

| 项目 | 数量 |
| - | - |
| 用户（task） | 56 |
| 子任务（subtask） | 771（外卖 delivery 404 · 到店 instore 223 · 酒旅 ota 144），每个用户约 14 个，按时间排序 |
| 带标准答案 `target_product_ids` 的子任务 | 766 |
| 考察偏好更新 `update` | 131（另有 16 个同时考察主动性） |
| 考察主动追问 `proactive` | 86 |

### 数据特色

- **指令模糊**：如「忙得脚不沾地，中午饭就帮我点个外卖来单位算了」，口味、忌口、配送时长都要从历史里推断。
- **偏好藏在噪声里**：每个子任务附带新的历史交互 `interactions`（对话 + 搜索/下单/浏览行为），其中混有大量无关闲聊。
- **偏好会变**：后面的子任务可能推翻前面的偏好（`update`），要以较新的记录为准。
- **干扰项精心设计**：每个外卖子任务约 43 家店、100 多件商品，只有 1 家目标店；干扰项往往只违反一条约束（配送 34 分钟 vs 要求 30 分钟内、组合套装 vs 单件、虾仁 vs 肉类）。
- **健康与生活约束**：如多囊卵巢综合征 → 避开高 GI、油炸、加工食品。

### 字段与可见性

| 字段 | 含义 | agent 能否看到 |
| - | - | - |
| `user_profile` | 职业、住址、疾病史等注册信息 | ✅ |
| `instruction` | 本次用户指令 | ✅（作为用户消息） |
| `interactions` | 本子任务新暴露的历史交互 | ✅（累积到当前子任务） |
| `environment` | 时间、天气、常用地址、商家/商品库 | ✅（商家商品需脱敏） |
| `environment.stores[*].store_type` / `products[*].product_type` / `distraction_reason` | 目标/干扰项标注及原因 | ❌ 答案泄漏 |
| `target_product_ids` / `rubric` / `evaluation_criteria` | 标准答案与评分细则 | ❌ 仅用于判分 |
| `user_scenario` / `historical_chat` / `historical_behavior` | 用户真实偏好的标准答案 | ❌ |
| `noise` / `user_intention` | 噪声条目 / 主动追问才透露的隐藏意图 | ❌ |

### 官方评测规则（仅供参考，本项目未采用）

- 同一用户的子任务**按顺序**执行，子任务之间用新的 `interactions` 更新记忆并注入 agent 提示词；记忆后端有 Full Context / Agentic（Rewrite）/ RAG 等。
- 每个子任务是**多轮对话**：用户模拟器（gpt-4.1）故意回答模糊，agent 调官方 66 个工具查询、下单。
- LLM 评审（gpt-4.1）按 rubric 逐条判定，**全部满足才得 1 分**；每题跑 4 次，报告 Avg@4 / Pass@4 / Pass^4。
- 排行榜上最好成绩约 0.50 Avg@4（Claude-Opus-4.6，Full Context），Doubao-Seed-2.0-pro 为 0.428（非思考）/ 0.474（思考）。

### 本项目的评测规则（练手简化版）

目的是对比框架，不是冲榜，因此只用数据，工具、流程、判分全部自己定义并由各框架共用（`bench/`）：

- **范围**：只做外卖（delivery）子任务；默认跳过 `proactive`（单轮无法追问，`--include-proactive` 可纳入）。
- **单轮**：系统提示词给出环境、用户画像、历史交互，用户消息为 `instruction`，agent 调工具后提交一份结构化决策 `Decision`（store_id、product_ids、送达地址、理由），不与用户多轮对话。
- **历史**：累积到当前子任务为止的全部 `interactions`，超过 `--history-chars`（默认 60000 字符）时从头截断、保留最近部分。
- **工具**：`search_stores` / `get_store_products` / `search_products`，只读查询脱敏后的商家库。查询逻辑在 `bench/env.py`，各框架按自己的风格包装成工具，工具说明一字不差照抄。
- **模型**：`config.py` 统一配置（默认 `doubao-seed-2.0-lite`，temperature 0.1，关闭深度思考）。
- **判分**（`bench/runner.py`）：
  - 命中率 hit：选中商品覆盖全部 `target_product_ids`；
  - 精确率 exact：与目标商品集合完全一致；
  - 召回 recall：选中的目标商品占比（多件商品的子任务给部分分）；
  - 另记 LLM 调用次数、工具调用次数、token、耗时。
- **注意**：规则简化后分数与官方排行榜不可比，只用于本项目各框架之间横向对比。

## 目录与运行

```
run.py               # 唯一入口：加载一次子任务，依次交给各框架评测
config.py            # 模型连接与统一采样参数
bench/               # 与框架无关的共用部分：数据加载与脱敏、商家库查询、提示词变量、运行记录 RunRecord、判分
fw_pydantic/         # 各框架只实现 solve(case) -> RunRecord：怎么跑一次 agent、怎么从结果里取开销
fw_openai_agents/
fw_langgraph/
results/             # 每个子任务一行明细：<框架>-<时间>.jsonl
```

提示词模板 `system.md`、最终输出结构 `Decision`、工具说明都是 agent 的组成部分，放在各框架目录内、按框架自己的方式定义与注入；**三个框架的这些内容必须一致**，改一份要同步另外两份，否则对比不公平。`bench/prompt.py` 只负责把子任务整理成模板变量，`bench/record.py` 的 `RunRecord` 是 solve 交给评测的记录（决策以字典形式交出，不依赖任何框架的类）。

框架目录统一加 `fw_`（framework）前缀：不能与库同名（`pydantic`、`langgraph`、`agents`、`openai`），否则会遮蔽真正的库。

```bash
pdm run python run.py pydantic                                   # 第一个用户的全部外卖子任务
pdm run python run.py pydantic openai_agents langgraph --limit 3 # 多个框架依次跑同一批子任务
pdm run python run.py langgraph --users A891207 U901652 --history-chars 80000
```

## pydantic

按 nebula 项目的 Pydantic AI 约定组织：

| 文件 | 职责 |
| - | - |
| `fw_pydantic/agent.py` | 装配层：唯一的 `Agent`（加载 `system.md`，`instructions=` 函数每次请求现渲染、`tools=`、`output_type=final_answer`）与模型构建；豆包 `tool_choice=required` 空响应问题在客户端出口降级为 `auto` |
| `fw_pydantic/tools.py` | 工具函数，第一个参数 `RunContext[Deps]` 由框架注入、不进 schema，经 `ctx.deps.env` 查商家库 |
| `fw_pydantic/output.py` | 最终输出结构 `Decision`，以及 `final_answer` 输出工具（`ToolOutput(Decision)`）的名字与描述 |
| `fw_pydantic/deps.py` | 依赖注入 `Deps(case, env)` |
| `fw_pydantic/solve.py` | 运行层：每个子任务构造 Deps、`agent.run_sync`，从 `capture_run_messages()` 统计开销 |

要点：结构化输出走「输出工具」，模型只输出文本时框架会自动要求重试；校验失败也会把错误回传给模型重试。

## open AI Agent SDK

| 文件 | 职责 |
| - | - |
| `fw_openai_agents/agent.py` | `Agent` 是一份声明式配置：动态 `instructions`（函数，每次调模型前用 `system.md` 现渲染）、`@function_tool` 工具（`RunContextWrapper[DeliveryContext]` 注入本地上下文）、`final_answer` + `StopAtTools`、`ModelSettings` |
| `fw_openai_agents/solve.py` | 运行层：`Runner.run_sync` 驱动循环；模型只回文本时用 `result.to_input_list()` 续上对话追问；开销取自 `raw_responses` / `new_items` |

踩过的坑：

- 默认会把 trace 上传到 OpenAI 平台，必须 `set_tracing_disabled(True)`；网关只兼容 Chat Completions，需用 `OpenAIChatCompletionsModel`。
- `output_type` 走 `response_format` 的 JSON Schema 约束，豆包网关不遵守，模型照样输出自然语言 → 解析失败；改为 `final_answer` 工具 + `StopAtTools`。
- `StopAtTools` 的 `final_output` 是工具返回值**转成的字符串**，不是原对象，需要自己解析回 `Decision`。
- 非字符串的工具返回值会被 `str()` 成 Python repr，工具统一返回 JSON 字符串。
- `@function_tool` 以 `decision: Decision` 为参数时会生成嵌套 schema，改用手写 `FunctionTool` 直接以 `Decision` 的扁平字段为参数，与其他框架一致。

## langgraph

`fw_langgraph/graph.py` 把 ReAct 循环显式画成状态图，`fw_langgraph/solve.py` 用 `graph.stream(stream_mode='values')` 运行，开销取自最后一个 State 的 `AIMessage.usage_metadata`：

```
START → agent ─┬─ 调查询工具 → tools（ToolNode）──→ agent
               ├─ 调 Decision → respond ─┬─ 参数合法 → END
               │                         └─ 校验失败 → agent（带错误重试）
               └─ 只输出文本 → remind ──→ agent
```

要点：`State`（消息 + 决策）在图中流转；`Context`（case、商家库）通过 `context_schema` 声明，节点用 `Runtime[Context]`、工具用 `ToolRuntime[Context]` 注入，不进 State 也不发给模型；最终决策用「把 `Decision` 也绑成工具」的方式提交；系统提示词用 LangChain 的 `ChatPromptTemplate`（`system.md` + `MessagesPlaceholder`）与模型以 `prompt | llm` 串成链，每轮现渲染、不写进 State。LangChain 的 `create_agent` 封装了同样的循环，这里手写图是为了看清 LangGraph 本身的概念。

## 自制 LLM loop

## 首轮对比（2026-09-28，用户 A891207 的 7 个外卖子任务，各跑 1 次）

| 框架 | 命中率 | 召回 | 平均 LLM 调用 | 平均工具调用 | 平均输入 tokens | 平均耗时 |
| - | - | - | - | - | - | - |
| pydantic-ai | 2/7 | 28.6% | 3.6 | 2.6 | 12.9 万 | 16.0s |
| OpenAI Agents SDK | 0/7 | 9.6% | 4.7 | 3.7 | 17.5 万 | 20.6s |
| LangGraph | 2/7 | 38.1% | 4.6 | 3.6 | 16.7 万 | 19.7s |

样本太少、单次运行波动大（各框架命中的题互不重合，同一框架前后两次结果也不同），暂不能据此评判框架优劣。失败几乎都是模型本身选错：没有逐条核对明确条件（配送时长、规格、漏买），没有用上历史里的个性化偏好。
