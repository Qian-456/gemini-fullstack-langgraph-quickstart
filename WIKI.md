# Gemini Fullstack LangGraph Quickstart (二开) - Code Wiki

## 1. 项目概述 (Project Overview)
本项目是基于 Gemini Fullstack LangGraph Quickstart 的二次开发版本。项目构建了一个具备网络搜索（WebSearch）和深度研究（Research）能力的智能体应用。前端基于 React + Vite 构建，后端基于 LangGraph + FastAPI 构建，默认接入通义千问（DashScope API）和 Tavily 搜索引擎。

核心功能包括：
- **普通对话**：直接基于大模型回答并保持上下文。
- **WebSearch**：通过大模型工具调用进行轻量级联网信息获取。
- **Research 深度研究**：当话题需要深入了解时，进入深度研究子流程（多轮检索、反思归纳、总结输出）。

---

## 2. 项目架构 (Project Architecture)

### 2.1 整体架构
- **前端 (Frontend)**：React + Vite + Tailwind CSS。使用 `@langchain/langgraph-sdk/react` 的 `useStream` Hooks 实时与后端通信，管理对话状态并渲染研究流程的时间线（Activity Timeline）。
- **后端 (Backend)**：Python + LangGraph。主控制流为一个状态图（StateGraph），根据用户意图进行普通回复或路由到包含查询生成、多次搜索、结果反思和最终汇总的“深度研究（Research）”图。并使用 FastAPI 提供前端静态文件托管支持。

### 2.2 目录结构
```text
/workspace/
├── backend/                  # 后端项目根目录
│   ├── src/agent/            # Agent 核心逻辑代码
│   ├── examples/             # 脚本与示例（如 CLI 执行脚本）
│   ├── tests/                # 单元测试与 E2E 测试
│   ├── langgraph.json        # LangGraph 部署配置文件
│   ├── pyproject.toml        # 后端依赖与工程配置
│   └── .env.example          # 后端环境变量示例
├── frontend/                 # 前端项目根目录
│   ├── src/                  # 核心源码 (组件、库、App 路由等)
│   ├── package.json          # 前端依赖配置
│   └── vite.config.ts        # Vite 构建配置
├── Dockerfile                # Docker 镜像构建文件
├── docker-compose.yml        # Docker Compose 部署配置
└── README.md                 # 项目说明文件
```

---

## 3. 主要模块职责 (Main Module Responsibilities)

### 3.1 后端模块 (`backend/src/agent/`)
- **`graph.py`**: 主状态图模块。定义了核心的 `StateGraph`，包含大模型主节点（`agent_node`）和工具执行节点（`tools_node`）。处理判断进入工具调用、常规对话或是直接移交到研究流程。
- **`subgraph.py`**: 研究子流程模块。包含深度研究的具体节点实现：生成搜索词（`generate_query`）、执行搜索（`web_research`）、评估信息并生成跟进搜索（`reflection`）、输出最终答案（`finalize_answer`）。
- **`state.py`**: 状态定义模块。定义了在 LangGraph 中流转的数据结构，如 `OverallState`、`ReflectionState` 等，使用 `TypedDict` 和 `Annotated` 进行状态字段合并。
- **`configuration.py`**: 配置管理模块。定义模型参数、循环限制、并发配置等（支持通过 `RunnableConfig` 传入或从环境变量读取）。
- **`app.py`**: FastAPI 应用扩展模块。通过 `FastAPI` 挂载前端构建后的静态文件，并配合 `langgraph.json` 实现 API 与前端的同源部署。
- **`tools_and_schemas.py`**: Pydantic Schema 与工具类型定义。用于约束 LLM 的结构化输出。
- **`utils.py`**: 工具类。包含处理 Tavily 搜索结果、解析 JSON、提取 URL 等工具函数。

### 3.2 前端模块 (`frontend/src/`)
- **`App.tsx`**: 核心视图组件。负责管理聊天流状态、维护时间线（Activity Timeline）以及协调各子组件。
- **`components/ActivityTimeline.tsx`**: 研究流程时间线组件。用于展示后端推流发出的 `generate_query`、`web_research` 等事件的实时进度。
- **`components/ChatMessagesView.tsx`**: 聊天消息列表组件。负责渲染用户与 AI 的历史对话内容。
- **`components/InputForm.tsx`**: 用户输入组件。接收用户指令并配置研究深度（Effort）。
- **`lib/uiMode.ts`**: UI 模式计算逻辑。根据后端传递的事件流判断当前应用处于 `chat` 还是 `research` 模式。
- **`lib/activityTimeline.ts`**: 处理和整合事件流到时间线数据结构的工具库。

---

## 4. 关键类与函数说明 (Key Classes & Functions)

### 4.1 后端关键节点与函数
- **`agent_node`** ([backend/src/agent/graph.py](file:///workspace/backend/src/agent/graph.py))
  主 Agent 节点。接收当前的对话状态（`OverallState`），通过绑定的模型（`ChatTongyi`）和工具（`web_search_tool`, `handoff_research_tool`）决定是直接回答还是生成工具调用。
- **`tools_node`** ([backend/src/agent/graph.py](file:///workspace/backend/src/agent/graph.py))
  工具执行节点。如果上一步大模型生成了 `handoff_research` 调用，该节点会返回 `Command(goto="generate_query", ...)` 跳转指令，从而将控制权转移到研究子流程。
- **`generate_query`** ([backend/src/agent/subgraph.py](file:///workspace/backend/src/agent/subgraph.py))
  生成研究查询节点。利用大模型的结构化输出能力，将用户宽泛的问题拆解为多个具体的搜索 Query。
- **`web_research`** ([backend/src/agent/subgraph.py](file:///workspace/backend/src/agent/subgraph.py))
  网络研究节点。调用 `TavilyClient` 根据传入的查询词获取搜索结果，并将结果进行整合汇总。
- **`reflection`** ([backend/src/agent/subgraph.py](file:///workspace/backend/src/agent/subgraph.py))
  反思评估节点。评估当前搜集到的信息是否足以回答用户问题，如果不足则生成进一步的 Follow-up 查询，并增加 `research_loop_count`。
- **`evaluate_research`** ([backend/src/agent/subgraph.py](file:///workspace/backend/src/agent/subgraph.py))
  条件边函数（Conditional Edge）。基于 `reflection` 的输出和最大循环次数（`max_research_loops`），决定是回到 `web_research` 还是进入 `finalize_answer`。
- **`finalize_answer`** ([backend/src/agent/subgraph.py](file:///workspace/backend/src/agent/subgraph.py))
  组装答案节点。将收集到的所有搜索摘要和来源整合，利用模型输出带引用的最终长篇回答。

### 4.2 前端关键 Hooks 与逻辑
- **`useStream`** (来自 `@langchain/langgraph-sdk/react`)
  在 [App.tsx](file:///workspace/frontend/src/App.tsx) 中用于连接 LangGraph API。该 hook 的 `onUpdateEvent` 会实时捕获后端节点的状态更新（如 `generate_query`, `reflection`），并触发前端界面的变化。
- **`filterWebSearchToolMessages`** ([frontend/src/lib/messageVisibility.ts](file:///workspace/frontend/src/lib/messageVisibility.ts))
  用于过滤对话记录，隐藏系统内部生成的带有 JSON 或结构化数据、不需要暴露给用户的 Tool Call 消息记录。

---

## 5. 依赖关系 (Dependencies)

### 5.1 后端依赖 (`backend/pyproject.toml`)
- **LangChain / LangGraph 生态**: `langgraph`, `langchain`, `langchain-community`, `langgraph-sdk`, `langgraph-api`, `langgraph-cli` 等。
- **LLM 与搜索**: `dashscope` (通义千问模型 API), `tavily-python` (Tavily Web Search 引擎)。
- **Web 服务**: `fastapi` (提供前端静态托管支持及自定义路由)。
- **其他**: `python-dotenv` (读取环境变量)。

### 5.2 前端依赖 (`frontend/package.json`)
- **框架与构建**: `react`, `react-dom`, `vite`, `typescript`。
- **LangChain SDK**: `@langchain/core`, `@langchain/langgraph-sdk`。
- **UI 组件与样式**: `tailwindcss`, `@tailwindcss/vite`, `clsx`, `tailwind-merge`, `lucide-react`。
- **Radix UI**: 提供无障碍底层组件，如 `@radix-ui/react-scroll-area`, `@radix-ui/react-select` 等。

---

## 6. 项目运行方式 (How to Run the Project)

### 6.1 前置要求
- **Node.js**: v18+ 与 npm
- **Python**: v3.11+
- 必需的环境变量：`DASHSCOPE_API_KEY` 和 `TAVILY_API_KEY`。

### 6.2 本地开发 (Local Development)

1. **环境配置**：
   在 `backend` 目录下复制并编辑配置文件：
   ```bash
   cd backend
   cp .env.example .env
   # 在 .env 中填入 DASHSCOPE_API_KEY 与 TAVILY_API_KEY
   ```

2. **启动后端**：
   安装依赖并启动 LangGraph 开发服务器：
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -e .
   langgraph dev
   ```
   后端服务默认启动在 `http://127.0.0.1:2024`。

3. **启动前端**：
   在新的终端窗口中：
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   前端服务默认启动在 `http://localhost:5173`。浏览器访问 `http://localhost:5173/app` 即可使用。

### 6.3 生产/Docker 部署 (Docker Compose)
项目提供了一键容器化运行环境，集成了 Postgres（用于持久化状态/线程记忆）和 Redis（用于后台任务流处理）。

构建并启动：
```bash
docker build -t qwen-fullstack-langgraph -f Dockerfile .

DASHSCOPE_API_KEY="your_dashscope_api_key" \
TAVILY_API_KEY="your_tavily_api_key" \
LANGSMITH_API_KEY="your_langsmith_api_key" \
docker-compose up
```
启动后可通过 `http://localhost:8123/app/` 访问应用。

### 6.4 纯后端命令行测试 (CLI Testing)
可以不启动前端，直接通过命令行测试 Agent 流程：
```bash
cd backend
python examples/cli_research.py "什么是可再生能源的最新趋势？"
```
