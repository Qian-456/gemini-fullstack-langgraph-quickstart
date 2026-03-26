# 通义千问(Qwen) + Tavily Search 替换 Spec

## Why
当前后端依赖 Gemini（模型与原生 Google Search 工具），在国内网络与合规场景下使用受限。需要以最小改动切换到阿里通义千问（DashScope/Qwen）并将网页检索切换为 Tavily Search。

## What Changes
- 将后端 LLM 从 `ChatGoogleGenerativeAI` 切换为通义千问的 Chat 模型实现（保持 LangChain 接口与结构化输出能力）。
- 将 Web 检索从 `google.genai` 的 `google_search` 工具调用切换为 Tavily Search API。
- 调整“引用/来源”链路：不再依赖 Gemini 的 `grounding_metadata`，改为基于 Tavily 返回的 `title/url/content` 生成可点击来源链接。
- 更新提示词以去除对 Vertex/Gemini grounding URL 格式的强依赖，仍要求最终答案包含来源链接（Markdown）。
- 更新配置项默认模型名（从 `gemini-*` 变更为 `qwen-*` 或 DashScope 对应名称）。
- 新增/替换环境变量：移除 `GEMINI_API_KEY` 强依赖，新增 `DASHSCOPE_API_KEY`（或等价命名）与 `TAVILY_API_KEY`。
- 更新依赖清单与容器环境变量透传（docker-compose）。
- 补充/更新测试，采用 TDD：先写测试再实现。

## Impact
- Affected specs:
  - LLM Provider（Gemini → Qwen）
  - Web Search Provider（Google native tool → Tavily）
  - Citation/Sources Formatting（grounding → search results）
- Affected code:
  - `backend/src/agent/graph.py`（LLM 初始化与 `web_research` 实现）
  - `backend/src/agent/utils.py`（`get_citations/resolve_urls/insert_citation_markers` 适配）
  - `backend/src/agent/prompts.py`（提示词去耦与引用要求）
  - `backend/src/agent/configuration.py`（默认模型名与可配置项）
  - `backend/pyproject.toml`（依赖切换/新增）
  - `backend/.env.example`、`backend/.env`、`docker-compose.yml`（配置与透传）
  - `backend/examples/cli_research.py`（如仍引用 Gemini 默认模型需同步）

## ADDED Requirements
### Requirement: Qwen 模型支持
系统 SHALL 支持通过环境变量配置通义千问（DashScope/Qwen）的 API Key，并使用通义千问 Chat 模型完成查询生成、反思与最终答案生成。

#### Scenario: 使用 Qwen 生成查询与答案
- **WHEN** 用户发起一次研究型提问
- **THEN** 系统使用通义千问模型生成 search queries、反思是否需要补充搜索、并生成最终答案
- **AND** 不需要设置 `GEMINI_API_KEY`

### Requirement: Tavily Search 网页检索
系统 SHALL 使用 Tavily Search 执行网页检索，并将搜索结果整理为可被后续总结的文本片段。

#### Scenario: 搜索成功并产生可追溯来源
- **WHEN** `web_research` 针对某个 query 执行检索
- **THEN** 返回的研究结果文本包含来源链接（Markdown）
- **AND** `sources_gathered` 结构中包含可去重的来源项（至少包含 title 与 url）

## MODIFIED Requirements
### Requirement: 引用与来源生成机制
系统 SHALL 继续在最终答案中输出来源链接，但引用数据 SHALL 来自 Tavily 的搜索结果而非 Gemini grounding metadata。

#### Scenario: 最终答案仍包含来源链接
- **WHEN** 系统生成最终答案
- **THEN** 输出文本中包含来自 `web_research_result` 的来源链接
- **AND** `finalize_answer` 进行来源去重与链接替换/展开（如存在短链策略）

## REMOVED Requirements
### Requirement: 依赖 Gemini grounding_metadata 的引用生成
**Reason**: Tavily Search 不提供 Gemini grounding_metadata 结构，且 Google Search 工具依赖 `google.genai`。
**Migration**: 将 `get_citations/resolve_urls/insert_citation_markers` 的输入改为 Tavily 结果结构；提示词改为要求在汇总时保留来源链接。
