# PR Review 检查清单

> **职责**: PR Review 检查清单的**单一真实源**，涵盖架构、组件设计、代码风格、安全、测试和性能检查项。

---

## 分层与架构

- [ ] 新文件放置在正确的 FSD 层级
- [ ] 依赖方向正确（只向下依赖）
- [ ] 没有跨 feature 的直接导入
- [ ] shared 层没有业务逻辑
- [ ] 每个 slice 有 `index.ts` 统一导出

详见 [architecture.md](architecture.md)

---

## 组件设计

- [ ] 组件类型正确（展示/容器/复合）
- [ ] Props 使用 interface 定义
- [ ] 事件处理函数命名以 `handle` 开头
- [ ] children 类型为 `React.ReactNode`
- [ ] 可选 Props 有合理默认值
- [ ] 复合组件使用 Context 共享状态

详见 [component-design.md](component-design.md)

---

## 代码风格

- [ ] 命名符合规范
- [ ] 没有 `any` 类型
- [ ] Props 使用 `interface` 定义
- [ ] 导入按规范排序
- [ ] 没有未使用的变量/导入

详见 [code-style.md](code-style.md)

---

## 状态管理

- [ ] 服务端数据使用 React Query
- [ ] 全局状态使用 Zustand
- [ ] Store 有 selector hooks 导出
- [ ] Query Keys 遵循命名规范
- [ ] 敏感数据不存入持久化 Store

详见 [state-management.md](state-management.md)

---

## 安全

- [ ] 没有 `dangerouslySetInnerHTML` (除非必要且使用 DOMPurify)
- [ ] 没有 `eval()`, `new Function()`
- [ ] URL 跳转有验证
- [ ] 用户输入有验证和限制
- [ ] 敏感数据不在 localStorage
- [ ] 没有硬编码的密钥

详见 [security.md](security.md)

---

## 测试

- [ ] 测试文件与组件同目录
- [ ] 使用可访问性查询
- [ ] 异步操作正确等待
- [ ] Mock 仅边界依赖
- [ ] 覆盖率达标 (≥80%)

详见 [testing.md](testing.md)

---

## 性能

- [ ] 路由级组件使用 lazy 加载
- [ ] 大列表使用虚拟列表
- [ ] memo 使用有明确理由
- [ ] 图片有 loading="lazy"

详见 [performance.md](performance.md)

---

## 无障碍

- [ ] 图片有描述性 alt 文本
- [ ] 表单控件有关联的 label
- [ ] 可交互元素可通过键盘访问
- [ ] 颜色对比度 >= 4.5:1
- [ ] 图标按钮有 `aria-label`

详见 [accessibility.md](accessibility.md)

---

## 项目结构

- [ ] 新文件放置在正确的 FSD 层级
- [ ] 组件与测试文件同目录
- [ ] 新 slice 有 `index.ts` 导出
- [ ] 无临时文件被提交
- [ ] 环境变量已在 `.env.example` 声明

详见 [project-structure.md](project-structure.md)

---

## 预提交一键验证

```bash
pnpm lint && pnpm format:check && pnpm typecheck && pnpm test:coverage
```
