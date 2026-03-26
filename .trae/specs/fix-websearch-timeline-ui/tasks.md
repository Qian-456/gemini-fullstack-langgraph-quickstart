# Tasks
- [x] Task 1: 为 timeline 聚合与轮次隔离补齐前端测试（TDD）
  - [x] SubTask 1.1: 引入并配置最小前端测试框架（优先 Vitest）
  - [x] SubTask 1.2: 抽取纯函数实现“事件聚合/去重/更新”逻辑以便单测
  - [x] SubTask 1.3: 编写单测覆盖 Web Research 去重与“最新事件覆盖”行为
  - [x] SubTask 1.4: 编写单测覆盖 runId 隔离与历史快照不可变

- [x] Task 2: 实现 Web Research 去重与 runId 归属隔离
  - [x] SubTask 2.1: 在 `App.tsx` 引入 runId 并在 submit 时重置 live timeline
  - [x] SubTask 2.2: 在 `onUpdateEvent` 中基于 runId 过滤事件并按类型聚合更新
  - [x] SubTask 2.3: 在 finalize 时写入历史快照并避免后续改写
  - [x] SubTask 2.4: 必要时调整 `ChatMessagesView`/`ActivityTimeline` 以匹配新行为

- [x] Task 3: 回归验证与体验确认
  - [x] SubTask 3.1: 运行前端测试与类型检查
  - [x] SubTask 3.2: 手动回归：首次搜索不出现两个 Web Research 条目
  - [x] SubTask 3.3: 手动回归：连续提问不串扰，历史 timeline 不被后续事件污染

# Task Dependencies
- Task 2 depends on Task 1
- Task 3 depends on Task 2
