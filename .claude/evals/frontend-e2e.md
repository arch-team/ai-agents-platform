## EVAL: frontend-e2e
Created: 2026-02-18

### Capability Evals

#### 认证流程 (auth.spec.ts)
- [ ] 未认证访问根路径重定向到 /login
- [ ] 登录页面正确渲染 (邮箱/密码输入 + 登录按钮)
- [ ] 正确凭证登录跳转到 Dashboard
- [ ] 错误凭证显示错误信息
- [ ] 登出跳转回登录页

#### 注册流程 (register.spec.ts)
- [ ] 注册页面正确渲染 (姓名/邮箱/密码/确认密码)
- [ ] 登录链接可跳转
- [ ] 注册成功跳转到登录页
- [ ] 注册失败显示错误信息

#### Dashboard (dashboard.spec.ts)
- [ ] 显示欢迎标题
- [ ] 显示统计卡片 (Agent 总数/对话总数/Team 执行)
- [ ] 显示快速操作区域
- [ ] 快速操作导航正确

#### 全局导航 (navigation.spec.ts)
- [ ] 侧边栏显示所有 9 个导航链接
- [ ] 点击链接导航到对应页面
- [ ] 页面标题正确
- [ ] 移动端汉堡菜单可见

#### Agent 管理 (agents.spec.ts)
- [ ] Agent 列表显示所有 Agent
- [ ] 显示不同状态 (草稿/已激活/已归档)
- [ ] 创建 Agent 表单提交成功
- [ ] 点击 Agent 导航到详情页
- [ ] 详情页显示配置信息

#### 对话 (chat.spec.ts)
- [ ] 对话列表侧边栏可见
- [ ] 新建对话按钮可见
- [ ] 已有对话列表正确显示
- [ ] 未选择对话时显示提示
- [ ] 空对话列表显示空状态

#### 团队执行 (team-executions.spec.ts)
- [ ] 新建执行表单可见 (Agent 选择 + 提示词 + 提交按钮)
- [ ] 执行历史列表正确显示
- [ ] 空历史显示空状态
- [ ] 未选择记录时显示右侧提示

#### 知识库 (knowledge.spec.ts)
- [ ] 列表页标题和创建按钮可见
- [ ] 知识库列表正确显示
- [ ] 状态筛选下拉框可见
- [ ] 空列表显示空状态
- [ ] ACTIVE 状态显示同步按钮

#### 模板 (templates.spec.ts)
- [ ] 列表页标题和创建按钮可见
- [ ] 模板列表正确显示
- [ ] 状态筛选可见
- [ ] 空列表显示空状态
- [ ] 草稿模板显示删除按钮

#### 工具目录 (tools.spec.ts)
- [ ] 列表页标题和注册按钮可见
- [ ] 工具列表正确显示
- [ ] 状态和类型筛选可见
- [ ] 空列表显示空状态

#### 评估 (evaluation.spec.ts)
- [ ] 列表页标题和创建按钮可见
- [ ] 测试集列表正确显示
- [ ] 状态筛选可见
- [ ] 空列表显示空状态
- [ ] 草稿测试集显示激活和删除按钮

#### 使用洞察 (insights.spec.ts)
- [ ] 页面标题正确
- [ ] 时间范围选择器可见
- [ ] 概览统计卡片 (5 个指标)
- [ ] 使用趋势图区域可见
- [ ] Token 归因表格可见

#### 404 页面 (not-found.spec.ts)
- [ ] 不存在路径显示 404
- [ ] 返回首页按钮可见

### Regression Evals

#### 基础设施
- [ ] Playwright 配置正确 (baseURL, webServer, trace)
- [ ] Mock 数据覆盖所有 API 端点
- [ ] mockAll() 函数正确注册所有路由

#### 测试稳定性
- [ ] 所有测试使用 SPA 导航 (非 page.goto) 保持内存状态
- [ ] Mock 路由使用正则表达式匹配查询参数
- [ ] 状态值大小写与组件 StatusBadge CONFIG 一致

### Success Criteria
- pass@3 > 90% for capability evals (57 个 Playwright 测试)
- pass^3 = 100% for regression evals

### Test Commands
```bash
# 全量 E2E 测试
cd frontend && npx playwright test

# 单个模块
npx playwright test tests/e2e/auth.spec.ts
npx playwright test tests/e2e/agents.spec.ts
# ... 以此类推

# 列出所有测试
npx playwright test --list
```
