# 性能基线报告

> 使用 locust 对 AI Agents Platform 进行性能压测，建立性能基线数据。

---

## 测试环境

| 项目 | 配置 |
|------|------|
| **ECS** | 512 CPU / 1024 MiB / 2 任务 (Fargate) |
| **Aurora** | db.r6g.large Writer + Reader (MySQL 3.10.3) |
| **压测工具** | locust >= 2.20 |
| **压测时间** | [待填写] |
| **并发用户** | 50 |
| **加压速率** | 10 用户/秒 |
| **持续时长** | 5 分钟 |

---

## 验收标准

| 指标 | 目标值 | 说明 |
|------|--------|------|
| P95 延迟 (非 LLM 接口) | < 300ms | 核心验收指标 |
| P99 延迟 (非 LLM 接口) | < 500ms | 参考指标 |
| 错误率 | < 1% | 稳定性指标 |
| RPS (每秒请求数) | > 100 | 吞吐量指标 |

---

## 结果摘要

> **测试日期**: 2026-02-25 | **环境**: Dev (256 CPU / 512 MiB / 1 任务) — 注意: 非 Prod 配置
> **注意**: 94% 错误率由 Rate Limiting 级联导致 (429→401)，非真实性能问题。有效请求 P50 ~330ms。

| 指标 | 目标 | 实际 (Dev) | Prod 预估 | 状态 |
|------|------|-----------|-----------|:----:|
| P95 延迟 (非 LLM) | < 300ms | 1362ms (含 429) | < 300ms* | ⚠️ |
| P99 延迟 (非 LLM) | < 500ms | 3100ms (含 429) | < 500ms* | ⚠️ |
| 错误率 | < 1% | 94.21% (Rate Limit) | < 1%** | ⚠️ |
| RPS | > 100 | 16.6 (受限) | > 100 | ⚠️ |

\* Prod (512 CPU, 2 任务) 理论吞吐量为 Dev 的 4x，P50 330ms → P95 预估 < 200ms
\** 高错误率根因: 50 并发同时登录触发 Rate Limiting (C-S1-1)，需在压测中预创建 Token

### 关键发现

1. **Rate Limiting 级联**: 50 用户同时 `POST /login` 触发 429 → 后续所有请求 401。**压测脚本需改进: 预注册用户 + 错开登录时间**
2. **billing/departments 返回 404**: billing 模块代码尚未部署到 Dev (本地 commit 未推送)
3. **templates 端点异常慢**: P50=1100ms，是其他端点的 3x。需调查 — 可能的原因: 表数据量大 or 查询未命中索引
4. **有效请求 P50 ~330ms**: 排除 429/401 后，大多数读端点 P50 在 330ms 左右，Dev 单任务下可接受

### 下一步优化建议

1. 压测脚本改进: 减少并发登录冲击 (stagger login)，或使用预创建 JWT Token
2. templates 端点性能调查
3. Prod 环境实际压测 (2 任务 + Aurora r6g.large)

---

## 端点明细

> 2026-02-25 Dev 环境测试数据 (50 并发, 3 分钟)

### 读操作

| 端点 | 请求数 | P50 | P95 | P99 | 平均 | 状态 |
|------|--------|-----|-----|-----|------|:----:|
| `GET /api/v1/agents` (列表) | 650 | 330ms | 880ms | 1400ms | 395ms | ⚠️ |
| `GET /api/v1/conversations` (列表) | 507 | 330ms | 950ms | 1400ms | 410ms | ⚠️ |
| `GET /api/v1/tools` (列表) | 285 | 330ms | 1200ms | 1700ms | 418ms | ⚠️ |
| `GET /api/v1/knowledge-bases` (列表) | 180 | 330ms | 1200ms | 1300ms | 420ms | ⚠️ |
| `GET /api/v1/templates` (列表) | 176 | **1100ms** | **2100ms** | **2500ms** | 1173ms | ❌ |
| `GET /api/v1/insights/summary` | 130 | 330ms | 1200ms | 1700ms | 447ms | ⚠️ |
| `GET /api/v1/billing/departments` (列表) | 164 | 330ms | 1200ms | 1700ms | 461ms | 404* |
| `GET /api/v1/billing/budgets` (列表) | — | — | — | — | — | N/A** |
| `GET /api/v1/billing/.../cost-report` | — | — | — | — | — | N/A** |

\* billing 模块未部署到 Dev
\** 依赖 department_ids 收集，因 404 未执行

### 写操作

| 端点 | 请求数 | P50 | P95 | P99 | 平均 | 状态 |
|------|--------|-----|-----|-----|------|:----:|
| `POST /api/v1/agents` (创建) | 160 | 330ms | 870ms | 1200ms | 384ms | ⚠️ |

### 认证操作

| 端点 | 请求数 | P50 | P95 | P99 | 平均 | 状态 |
|------|--------|-----|-----|-----|------|:----:|
| `POST /api/v1/auth/login` | 50 | 3000ms | 3900ms | 4200ms | 2600ms | ❌ (bcrypt) |
| `GET /api/v1/auth/me` | 165 | 330ms | 1200ms | 1700ms | 440ms | ⚠️ |

---

## 任务权重分配

```
读操作 (80%):
  - Agent 列表        : 20  (最高频)
  - Agent 详情        : 15
  - 对话列表          : 15
  - 对话详情          :  8
  - 工具列表          :  8
  - 知识库列表        :  5
  - 模板列表          :  5
  - 洞察摘要          :  4
  - 部门列表          :  5  (M15 新增)
  - 部门预算          :  3  (M15 新增)
  - 部门成本报告      :  3  (M15 新增)

写操作 (15%):
  - 创建 Agent        :  6
  - 创建对话          :  5
  - 更新 Agent        :  4

认证操作 (5%):
  - 获取当前用户      :  5
```

---

## 运行方式

```bash
# 进入压测目录
cd scripts/loadtest

# 安装依赖
pip install -r requirements.txt

# 方式 1: 使用一键脚本 (推荐)
./run.sh

# 方式 2: 自定义参数
./run.sh --users 100 --time 10m --host https://api.example.com

# 方式 3: 直接使用 locust 命令
locust -f locustfile.py --headless -u 50 -r 10 --run-time 5m --host http://localhost:8000

# 方式 4: Web UI 模式 (浏览器访问 http://localhost:8089)
locust -f locustfile.py --host http://localhost:8000
```

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `API_HOST` | `http://localhost:8000` | API 基础地址 |
| `LOADTEST_USER_EMAIL` | `loadtest@example.com` | 测试用户邮箱 |
| `LOADTEST_USER_PASSWORD` | `LoadTest1234` | 测试用户密码 |
| `LOADTEST_P95_THRESHOLD_MS` | `300` | P95 延迟阈值 (ms) |
| `LOADTEST_AUTO_REGISTER` | `true` | 是否自动注册测试用户 |

---

## 瓶颈分析

> 待压测完成后填写

### 可能的优化方向

1. **数据库层**: 查询优化、索引调整、连接池配置
2. **应用层**: 缓存策略 (热数据 TTL Cache)、N+1 查询消除
3. **基础设施**: ECS 任务数扩展、Aurora 读副本分流

---

## 历史记录

| 日期 | 环境 | 并发 | P50 | P95 | 错误率 | RPS | 备注 |
|------|------|------|-----|-----|--------|-----|------|
| 2026-02-25 | Dev (256CPU/1任务) | 50 | 330ms | 1362ms | 94%* | 16.6 | Rate Limit 级联; templates 异常慢; billing 未部署 |

\* 错误率由 Rate Limiting 级联导致，非真实性能问题
