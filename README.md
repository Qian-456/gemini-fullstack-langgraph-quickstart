# Gemini Fullstack LangGraph Quickstart（二开）

这是一个基于 Gemini Fullstack LangGraph Quickstart 的二次开发项目：前端使用 React（Vite），后端使用 LangGraph + FastAPI，实现了一个可正常对话的智能体，并支持 WebSearch；当用户需要更深入的答案时，可以走 Research 流程对特定话题进行更深度的检索与归纳。

目前暂不支持流式回复（Streaming）。

<img src="./app.png" title="Fullstack LangGraph" alt="Fullstack LangGraph" width="90%">

## 你将获得什么

- 一个可用的聊天 UI（当前为非流式输出）。
- 一个“普通对话 + 可选深度研究”的 LangGraph 智能体：
  - 普通对话：直接回答并保持上下文。
  - WebSearch：需要联网时调用搜索工具补充信息。
  - Research：对话题进行更深入的多轮检索与归纳（按配置限制轮数）。
- 前后端本地开发热更新。
- 生产化部署示例（Docker Compose + Redis + Postgres）。

## 项目结构

- `frontend/`: React + Vite 前端
- `backend/`: LangGraph + FastAPI 后端（graph、tools、prompts、config）

## 本地开发快速开始

### 1) 前置条件

- Node.js 18+ 与 npm（或 pnpm/yarn）
- Python 3.11+
- API keys（用于联网搜索 / LLM 调用，具体以 `backend/.env.example` 为准）：
  - `DASHSCOPE_API_KEY`（Tongyi Qwen via DashScope）
  - `TAVILY_API_KEY`（Tavily web search）

可选：
- `make`（方便启动）。Windows 上更常见的方式是分别开两个终端运行前后端。

### 2) 配置环境变量

复制示例 env 文件并填写你的 keys：

```powershell
cd backend
copy .env.example .env
```

编辑 `backend/.env`：

```bash
DASHSCOPE_API_KEY="YOUR_ACTUAL_API_KEY"
TAVILY_API_KEY="YOUR_ACTUAL_API_KEY"
```

### 3) 安装依赖

后端：

```powershell
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\pip install -e .
```

前端：

```bash
cd frontend
npm install
```

### 4) 启动开发服务

推荐（尤其 Windows）：分别使用两个终端运行。

终端 A（后端）：

```powershell
cd backend
.venv\Scripts\langgraph dev
```

终端 B（前端）：

```bash
cd frontend
npm run dev
```

打开：

- 前端：`http://localhost:5173/app`
- 后端 API：`http://127.0.0.1:2024`

如果你本机可用 `make`，也可以一键启动：

```bash
make dev
```

## 配置说明

- 前端通过 `frontend/src/App.tsx` 里的 `apiUrl` 连接后端。
  - 开发环境默认：`http://localhost:2024`
  - Docker Compose 默认：`http://localhost:8123`
- 后端从 `backend/.env`（通过 `python-dotenv` 加载）或系统环境变量读取配置。

## Agent 工作方式

LangGraph 主图定义在 `backend/src/agent/graph.py`：

<img src="./agent.png" title="Agent Flow" alt="Agent Flow" width="50%">

高层流程（按需触发）：

1. 普通对话：直接生成回答。
2. 需要联网信息时：触发 WebSearch 获取来源。
3. 用户需要更深度时：进入 Research 流程，对话题进行多轮检索与归纳（有最大轮数限制）。

## CLI 示例

不启动前端，直接命令行执行后端智能体：

```bash
cd backend
.venv\Scripts\python examples/cli_research.py "What are the latest trends in renewable energy?"
```

## 测试

后端：

```powershell
cd backend
.venv\Scripts\pip install pytest
.venv\Scripts\pytest -q
```

前端：

```bash
cd frontend
npm test
```

## 部署（Docker Compose）

生产环境中，后端会服务化地提供优化后的前端静态资源。LangGraph 部署需要：

- Redis（用于后台任务的输出推送）
- Postgres（用于 assistants/threads/runs、线程状态与长期记忆、后台队列状态）

从项目根目录构建镜像：

```bash
docker build -t qwen-fullstack-langgraph -f Dockerfile .
```

启动：

```bash
DASHSCOPE_API_KEY=<your_dashscope_api_key> \
TAVILY_API_KEY=<your_tavily_api_key> \
LANGSMITH_API_KEY=<your_langsmith_api_key> \
docker-compose up
```

PowerShell：

```powershell
$env:DASHSCOPE_API_KEY="<your_dashscope_api_key>"
$env:TAVILY_API_KEY="<your_tavily_api_key>"
$env:LANGSMITH_API_KEY="<your_langsmith_api_key>"
docker-compose up
```

打开：

- App：`http://localhost:8123/app/`
- API：`http://localhost:8123`

备注：

- Docker Compose 示例需要 `LANGSMITH_API_KEY`。
- 如果你将后端暴露到公网，请更新 `frontend/src/App.tsx` 的 `apiUrl` 指向你的实际域名/地址。

## 技术栈

- React + Vite
- Tailwind CSS + shadcn/ui
- LangGraph + FastAPI
- Tongyi Qwen（DashScope）
- Tavily Search

## License

Apache License 2.0，详见 [LICENSE](LICENSE)。
