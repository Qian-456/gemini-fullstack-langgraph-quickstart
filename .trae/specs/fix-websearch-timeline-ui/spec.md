# WebSearch Timeline 去重与归属修复 Spec

## Why
当前 Research timeline 会出现 Web Research 条目重复展示；在连续提问或事件流存在延迟的情况下，历史消息的 timeline 也可能被后续事件“污染”，造成用户理解成本与信任问题。

## What Changes
- 前端对同一轮请求的活动事件进行聚合：同一轮中 `Web Research` 仅保留 1 条，后续同类型事件到来时更新该条目的内容而非追加新条目。
- 引入“轮次标识（runId）”以隔离不同 submit 之间的事件流：仅允许当前 runId 的事件更新 live timeline。
- 在 `finalize_answer` 对应的 AI 消息产出后，将当前 live timeline 作为快照写入该 AI 消息的历史活动记录；快照写入后保持不可变。

## Impact
- Affected specs: Research timeline 的展示一致性、live/historical 归属规则
- Affected code: `frontend/src/App.tsx`、`frontend/src/components/ChatMessagesView.tsx`、`frontend/src/components/ActivityTimeline.tsx`（如需支持“更新而非追加”的展示）

## ADDED Requirements
### Requirement: Web Research 聚合展示
系统 SHALL 在同一轮请求的 timeline 中最多展示 1 个 `Web Research` 条目，并在收到新的 `web_research` 事件时更新该条目的数据。

#### Scenario: 同一轮产生多个 web_research 事件
- **WHEN** 后端在同一轮处理中多次发送 `web_research` 更新（例如多 query、多 loop）
- **THEN** timeline 中 `Web Research` 条目不重复增加
- **AND** `Web Research` 的展示数据以“最新一次事件”为准（来源数、示例 label 等）

### Requirement: Timeline 轮次隔离
系统 SHALL 保证不同 submit 之间的活动事件互不串扰。

#### Scenario: 上一轮事件延迟到达
- **WHEN** 用户发起新一轮 submit，而上一轮仍有延迟到达的活动事件
- **THEN** 延迟事件不会出现在新一轮的 live timeline 中

## MODIFIED Requirements
### Requirement: 历史活动快照不可变
系统 SHALL 在 `finalize_answer` 对应 AI 消息完成后，保存该轮活动 timeline 的快照到该 AI 消息的历史记录中；该历史快照后续不会因新事件到达而发生变化。

## REMOVED Requirements
无

