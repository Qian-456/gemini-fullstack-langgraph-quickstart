# 系统架构升级与优化演进路线图 (Tier 2+ Roadmap)

基于当前系统存在的“能跑但不够稳健”、“缺乏可观测性”以及“工程化不足”的核心问题，本路线图规划了四大优化分支。每个分支按照从易到难、从基础到高级的顺序拆解为具体的可执行步骤。

---

## 🚀 分支一：系统可靠性层建设 (System Reliability Layer)
**目标**：将系统从“脆弱的单点调用”升级为“具备容错和自愈能力的高可用系统”。

- **Step 1.1: 引入 Retry 与 Exponential Backoff 机制**
  - **动作**：使用 `tenacity` 库拦截所有外部依赖（LLM 调用、Tavily API 调用等）。
  - **标准**：配置最大重试次数（如 3 次）、指数退避时间（Exponential Backoff）和 Jitter（抖动），防止在网络波动时将请求全部打挂。
- **Step 1.2: 精细化错误分类与异常捕获 (Error Classification)**
  - **动作**：抽象统一的异常基类，针对底层抛出的异常进行映射分类。
  - **标准**：区分 `RateLimitError`（触发 Backoff）、`TimeoutError`（触发重试或降级）、`ContextLengthExceededError`（触发输入截断或清理）和 `AuthenticationError`（直接告警，不重试）。
- **Step 1.3: 引入断路器机制 (Circuit Breaker)**
  - **动作**：使用 `pybreaker` 等库或自定义中间件，为外部 API 包装熔断器。
  - **标准**：当某个外部服务（如 Tavily 或 DashScope）在短时间内错误率超过阈值（如 50%），触发熔断，快速失败或走 Fallback 逻辑，防止系统雪崩。

---

## 📊 分支二：可观测性与评估体系 (Metrics & Evaluation)
**目标**：做到“心中有数”，用数据支撑系统的稳定性与回答质量。

- **Step 2.1: 基础监控埋点 (Metrics 收集)**
  - **动作**：在请求级别、节点级别（Agent Node, Tool Node）注入时间戳统计与状态记录。
  - **标准**：统计核心指标：端到端延迟（End-to-End Latency）、各节点耗时（Node Latency）、大模型 Token 消耗（Token Usage）及成本（Cost estimation）。
- **Step 2.2: 业务指标看板与告警 (Dashboard & Alerting)**
  - **动作**：对接 Prometheus/Grafana 或 LangSmith 等可观测性平台。
  - **标准**：追踪业务关键指标，如 Fallback Rate（降级触发率）、WebSearch 工具调用成功率、Research 平均循环轮数。配置告警规则（如错误率突增时推送到钉钉/飞书）。
- **Step 2.3: 离线与在线评估基准 (Evaluation Benchmark)**
  - **动作**：建立系统的 Golden Dataset（包含数十个典型的普通对话与深度研究 Query）。
  - **标准**：引入 `Ragas` 或 `LangChain Evaluation`，定期跑批测试。衡量回答的 `Context Precision`（相关性）、`Faithfulness`（忠实度/幻觉率），以此评估 Prompt 调整或模型切换带来的影响。

---

## 🧠 分支三：多模型与高可用策略 (Multi-Model Strategy)
**目标**：打破单点模型依赖，实现降级容灾与成本性能的动态平衡。

- **Step 3.1: 统一 LLM 抽象层**
  - **动作**：在 `configuration.py` 与实例化逻辑中解耦具体的模型供应商（Provider）。
  - **标准**：支持通过工厂模式（Factory Pattern）动态实例化不同平台的 LLM（如 Qwen, DeepSeek, OpenAI, Anthropic 等），统一输入输出格式。
- **Step 3.2: 主备容灾与 Fallback 机制 (Primary / Backup)**
  - **动作**：在模型调用层实现 Fallback 链（Fallback Chain）。
  - **标准**：例如 `Primary: Qwen-Max` -> `Backup: DeepSeek-V3` -> `Fallback: Qwen-Plus`。当主模型遇到限流或服务宕机时，无缝且无感地切换到备用模型。
- **Step 3.3: 动态模型路由机制 (Cost-Performance Tradeoff)**
  - **动作**：根据任务的复杂度和性质，动态分配不同的模型。
  - **标准**：
    - 简单的意图识别、总结、基础对话使用廉价且快速的“小模型”（如 Qwen-Flash / GPT-4o-mini）。
    - 复杂的逻辑推理、Reflection、Finalize Answer 使用“大模型”（如 Qwen-Max / Claude-3.5-Sonnet）。

---

## 🔀 分支四：路由与意图识别工程化 (Tool / Routing Engineering)
**目标**：将松散的 Tool 调用和 Graph 分支重构为具有明确意图识别和扩展性的路由架构。

- **Step 4.1: 引入独立的意图分类节点 (Intent Classifier)**
  - **动作**：在进入 `agent_node` 之前，增加一个前置的 `routing_node`。
  - **标准**：使用小模型或 Semantic Router，将用户的 Query 明确分类为 `ChitChat`（闲聊）、`QuickQA`（简单问答/WebSearch）、`DeepResearch`（深度研究）等枚举意图。
- **Step 4.2: 显式路由策略 (Explicit Routing Strategy)**
  - **动作**：通过 `Intent Classifier` 的输出，使用 LangGraph 的 Conditional Edges 进行确定性路由。
  - **标准**：不再完全依赖大模型在单轮中的 Tool Calling 来决定走哪个流程。让结构更清晰：闲聊直接走普通 LLM 节点，需要检索的走工具节点，深度研究走 `research_subgraph`。
- **Step 4.3: 工具注册中心化与动态加载 (Tool Registry)**
  - **动作**：剥离 `tools_node` 中的硬编码 if-else 逻辑。
  - **标准**：实现一个 Tool Registry，支持根据分类出的 Intent 动态绑定（Bind）对应的工具集，缩小每次模型调用的上下文（减少 Token 消耗，提高 Tool Calling 准确率）。
