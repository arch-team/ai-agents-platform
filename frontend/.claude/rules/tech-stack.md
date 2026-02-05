> **职责**: 技术栈版本的单一真实源

# 前端技术栈 (Tech Stack)

## 核心依赖

| 技术 | 版本 |
|------|------|
| React | 18+ |
| TypeScript | 5+ |
| Vite | 5+ |
| TailwindCSS | 3+ |
| TanStack Query | 5+ |
| Zustand | 4+ |
| React Hook Form | 7+ |
| Zod | 3+ |

## 测试工具

| 技术 | 版本 |
|------|------|
| Vitest | 1+ |
| Testing Library | 14+ |
| MSW | 2+ |
| Playwright | 1+ |

## 开发工具

pnpm | ESLint | Prettier

## 可选 (按需引入)

react-window | web-vitals | rollup-plugin-visualizer

## 禁止使用

| 禁止 | 替代 |
|------|------|
| Redux, MobX | Zustand |
| lodash (全量) | lodash-es |

## 升级策略

- **主版本** (React, TS, Vite): 团队评审
- **次/补丁版本**: 自主升级 + 测试
