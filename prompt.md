❯ 我准备构建一个基于Python的后端项目，这个项目会使用Claude Code开发，请你帮我深度调研或者在GitHub上找到针对Python后端项目的编码规范的Claude Code rule     

/Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-agents-platform/.claude/rules/code-style.md
/Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-agents-platform/.claude/rules/code-standards.md
是Claude Code的Rule为Python的后端项目定义的代码规范，请结合Claude Code的上下文管理给出优化建议

这两文件是两个不同的架构规范的定义。我希望最终的架构规范采用的是 DDD + Modular Monolith + Clean Architecture 这种架构模式，请你综合这两个架构规范的定义markdown文件，最终形成新版本的架构规范，新的架构规范命名为architecture-backend.md，并以此作为Claude Code的Rule

/claude-md-improver /Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-agents-platform/.claude/rules/security.md 这里Docstring 规范 (Google                
  Style)会显得代码中注释臃肿，跟代码本身即注释的目标冲突，请你针对这个文件中关于代码注释的规范进行优化     



/Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-agents-platform/.claude/rules/testing.md
这个文件是关于Python的后端项目的测试规范，以Claude Code的Rule形式承载，请基于Claude Code上下文管理的最佳实践,分析这个规范文件进行优化

❯ 我准备构建一个基于Python的后端项目，这个项目会使用Claude Code开发，请你帮我深度调研或者在GitHub上找到针对Python后端项目的编码规范的Claude Code rule     

/Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-agents-platform/.claude/rules/code-style.md
/Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-agents-platform/.claude/rules/code-standards.md
是Claude Code的Rule为Python的后端项目定义的代码规范，请结合Claude Code的上下文管理给出优化建议

这两文件是两个不同的架构规范的定义。我希望最终的架构规范采用的是 DDD + Modular Monolith + Clean Architecture 这种架构模式，请你综合这两个架构规范的定义markdown文件，最终形成新版本的架构规范，新的架构规范命名为architecture-backend.md，并以此作为Claude Code的Rule

/claude-md-improver /Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-agents-platform/.claude/rules/security.md 这里Docstring 规范 (Google                
  Style)会显得代码中注释臃肿，跟代码本身即注释的目标冲突，请你针对这个文件中关于代码注释的规范进行优化     



/Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-agents-platform/.claude/rules/code-standards.md
这个文件是关于Python的后端项目的SDK使用规范，以Claude Code的Rule形式承载，请基于Claude Code上下文管理的最佳实践，分析这个规范文件可以优化的方案

/Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-agents-platform/.claude/PROJECT_CONFIG.md
这个文件是关于Python的后端项目的项目配置信息，请基于Claude Code上下文管理的最佳实践，我希望这个文件具备项目通用性，请给出改进方案

/claude-md-improver 当前项目中Claude Code的上下文管理的markdown文件相互之间的引用存在循环引入，引入关系不明确，请给出改进方案

/Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-agents-platform/.claude/rules/testing.md 这个Claude Code上下文管理的测试规范中的目录组织。如下：

## 1. 测试结构

### 目录组织

```
tests/
├── conftest.py           # 全局 Fixture
├── unit/                 # 单元测试 (Domain, Application)
│   ├── conftest.py
│   ├── domain/
│   └── application/
├── integration/          # 集成测试 (API, Repository)
│   ├── conftest.py
│   ├── api/
│   └── repositories/
└── e2e/                  # 端到端测试
    └── conftest.py
```
跟/Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-agents-platform/.claude/rules/architecture.md 中规范的模块结构模板，不匹配不符合最佳实践，请提供优化改进方案


## 6. 模块结构模板

### 6.1 目录结构

```
modules/{module}/
├── __init__.py             # 模块公开 API 导出
├── api/
│   ├── __init__.py
│   ├── endpoints.py        # FastAPI router
│   ├── dependencies.py     # 依赖注入函数
│   ├── middleware/         # 模块级中间件
│   │   └── __init__.py
│   └── schemas/
│       ├── __init__.py
│       ├── requests.py     # 请求模型
│       └── responses.py    # 响应模型
├── application/
│   ├── __init__.py
│   ├── dto/                # 数据传输对象
│   │   └── __init__.py
│   ├── interfaces/         # 端口接口 (模块内外部服务抽象，如 S3Client 接口)
│   │   └── __init__.py
│   ├── exceptions/         # 应用层异常
│   │   └── __init__.py
│   └── services/
│       ├── __init__.py
│       └── {entity}_service.py
├── domain/
│   ├── __init__.py
│   ├── entities/
│   │   ├── __init__.py
│   │   └── {entity}.py
│   ├── value_objects/
│   │   └── __init__.py
│   ├── services/           # 领域服务
│   │   └── __init__.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── {entity}_repository.py  # 接口
│   ├── events.py
│   └── exceptions.py
└── infrastructure/
    ├── __init__.py
    ├── persistence/        # 数据持久化
    │   ├── __init__.py
    │   ├── models/
    │   │   ├── __init__.py
    │   │   └── {entity}_model.py
    │   └── repositories/
    │       ├── __init__.py
    │       └── {entity}_repository_impl.py
    └── external/           # 外部服务适配器
        └── __init__.py
```

当前的Python的后端项目的Claude code 上下文管理规范包括rule都有了，在architecture.md中定义了src源代码的目录结构，也在testing.md中定义了定义了测试的代码的目录结构。但作为整体的Python的后端项目的目录结构规范应该提供什么样的规范要求呢？


/Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-agents-platform/infra    
  是基础设施即代码的子项目的Claude Code 上下文（context）管理的规范文件，请你综合Claude Code 上下文管理的最佳实践分析存在的问题，并给出优化方案