---
id: mysql-fk-shared-lock-sse-deadlock
trigger: "when SSE streaming endpoint does DB writes on parent table while DI session holds FK shared lock"
confidence: 0.9
domain: "database"
source: "session-observation-2026-02-28"
---

# MySQL InnoDB FK 共享锁 × SSE 流式响应行锁超时

## Action
SSE 流式响应中，不要在 stream_session 中 UPDATE 被 DI session FK 共享锁锁住的父表行。
改用独立短事务 + 原子 SQL 增量 (`SET col = col + N`)。

## Evidence
- 2026-02-28: 对话 #48 快速连续发 3 条消息，3 个 SSE stream 的 `_finalize_stream` 全部 Lock wait timeout (50s)
- 根因: DI session `INSERT messages (conversation_id=48)` FK 检查对 `conversations.id=48` 加共享锁，SSE 期间不释放
- stream_session `UPDATE conversations WHERE id=48` 需排他锁 → 等待 → 超时
- 修复: `increment_message_stats()` 用独立 session + `UPDATE SET col = col + N`，锁持有 ~1ms

## Pattern
```
长事务 (SSE/WebSocket) + FK INSERT → 父表共享锁不释放
→ 同父表 UPDATE 需排他锁 → Lock wait timeout
→ 解法: 统计更新解耦到独立短事务
```
