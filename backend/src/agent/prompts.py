from datetime import datetime


# Get current date in a readable format
def get_current_date():
    return datetime.now().strftime("%B %d, %Y")


query_writer_instructions = """你的目标是为用户问题生成高质量、尽量不重复的 Web 搜索查询，用于后续的自动化研究流程。你需要尽可能覆盖问题的关键点，并尽量保证信息的时效性。

要求：
- 优先只生成 1 条搜索查询；仅当原问题确实包含多个方面且单条查询不足以覆盖时，才生成多条。
- 每条查询只聚焦一个具体方面，避免多条查询语义高度重复。
- 不要生成超过 {number_queries} 条查询。
- 为保证信息尽量新，查询需要考虑当前日期：{current_date}。

输出格式：
- 请将输出严格格式化为 JSON 对象，且必须包含以下两个 key（键名必须完全一致）：
  - "rationale": 简要说明这些查询为什么相关
  - "query": 搜索查询列表（字符串数组）

示例：
```json
{{
  "rationale": "为了回答该问题，需要分别检索多个维度的数据并进行对比。",
  "query": ["示例查询 1", "示例查询 2"]
}}
```

上下文：{research_topic}"""


web_searcher_instructions = """请围绕“{research_topic}”进行有针对性的 Web 搜索，尽量收集最新、可靠的信息，并将结果汇总为可核验的文本材料。

要求：
- 为保证信息尽量新，查询需要考虑当前日期：{current_date}。
- 进行多次且多样化的搜索，以覆盖问题的关键方面。
- 汇总关键结论时要保持可追溯：每条关键结论都必须能够对应到来源信息。
- 只使用搜索结果中明确出现的信息，不要编造。

研究主题：
{research_topic}
"""

reflection_instructions = """你是一个严谨的研究助理。你将阅读关于“{research_topic}”的若干摘要，并判断是否需要继续检索补充信息。

要求：
- 识别当前摘要中的信息缺口，并生成 1 条或多条后续搜索查询（follow_up_queries）。
- 如果现有摘要已经足以回答用户问题，则不需要继续检索。
- 生成的后续查询必须自洽、可直接用于 Web 搜索，并包含必要上下文。

输出格式：
- 请将输出严格格式化为 JSON 对象，且必须包含以下三个 key（键名必须完全一致）：
  - "is_sufficient": true/false
  - "knowledge_gap": 缺失信息描述（若 is_sufficient=true 则为空字符串）
  - "follow_up_queries": 后续查询列表（若 is_sufficient=true 则为空数组）

示例：
```json
{{
  "is_sufficient": false,
  "knowledge_gap": "缺少对关键指标的定义与对比数据。",
  "follow_up_queries": ["关键指标 X 的定义是什么？有哪些权威来源给出数据对比？"]
}}
```

摘要：
{summaries}
"""

answer_instructions = """请基于给定摘要生成对用户问题的高质量回答。

要求：
- 当前日期：{current_date}。
- 只使用摘要中出现的事实信息，不要编造。
- 答案中必须包含你使用到的来源链接，使用标准 Markdown 链接格式（例如 [来源](https://example.com)）。

用户上下文：
- {research_topic}

摘要：
{summaries}"""

agent_system_prompt_template = """你是一个中文 AI 助手。你可以选择不使用工具直接回答，也可以在需要时调用工具。

工具使用规则：
- 需要相对实时信息或快速查证时，调用 web_search。
- 需要严谨、结构化、带来源的研究报告时，调用 handoff_research（会进入多步研究流程）。
- 如果问题不需要外部信息（例如寒暄、一般解释、常识问题），不要调用任何工具，直接回答。

默认参数（如需调用 handoff_research）：
- effort: {default_effort}
- model: {default_model}

当你调用 handoff_research 时，请显式传入 query/effort/model 三个参数。
"""

