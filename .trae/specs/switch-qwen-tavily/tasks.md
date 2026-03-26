# Tasks
- [x] Task 1: 为 Qwen 与 Tavily 适配补齐测试（TDD）
  - [x] SubTask 1.1: 为 `web_research` 结果格式编写单测（含来源链接）
  - [x] SubTask 1.2: 为来源去重/展开逻辑编写单测（覆盖 `finalize_answer` 行为）
  - [x] SubTask 1.3: 为配置与环境变量回退逻辑编写单测（缺少 key 时的报错/提示）

- [x] Task 2: 将 LLM 从 Gemini 切换为通义千问（最小改动）
  - [x] SubTask 2.1: 引入通义千问所需依赖并移除/降级 Gemini 强依赖
  - [x] SubTask 2.2: 更新 `Configuration` 默认模型名与可配置项
  - [x] SubTask 2.3: 替换 `graph.py` 中 3 处 LLM 初始化为通义千问实现

- [x] Task 3: 将 WebSearch 从 Google 原生工具切换为 Tavily Search
  - [x] SubTask 3.1: 在 `web_research` 中接入 Tavily Search 并生成研究文本
  - [x] SubTask 3.2: 适配 `utils.py` 的引用/来源生成逻辑到 Tavily 结果结构
  - [x] SubTask 3.3: 更新提示词，去除对 Vertex/Grounding 的格式假设

- [x] Task 4: 同步运行配置与示例
  - [x] SubTask 4.1: 更新 `backend/.env.example` 与 `backend/.env`（新增 key，移除 gemini key 强依赖）
  - [x] SubTask 4.2: 更新 `docker-compose.yml` 环境变量透传
  - [x] SubTask 4.3: 更新 `backend/examples/cli_research.py`（如仍引用 Gemini 默认模型）

- [x] Task 5: 验证与回归
  - [x] SubTask 5.1: 运行测试套件并修复失败项
  - [x] SubTask 5.2: 进行一次端到端研究问题回归（确保答案含来源链接）

# Task Dependencies
- Task 2 depends on Task 1
- Task 3 depends on Task 1
- Task 4 depends on Task 2
- Task 4 depends on Task 3
- Task 5 depends on Task 2
- Task 5 depends on Task 3
