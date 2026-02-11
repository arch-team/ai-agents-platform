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

/Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-agents-platform/infra/.claude/rules/tech-stack.md是基础设施即代码的子项目的Claude Code 上下文（context）管理的规范文件，结合Claude Code 上下文管理的最佳实践在不影响它的作用的情况下精简冗余信息

如下是对/Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-agents-platform/infra    
是基础设施即代码的子项目的Claude Code 上下文（context）管理的规范文件的作用说明。请根据这个文件的作用说明。检查这些文件的内容是否存在违反了单一职责原则
.claude/
├── README.md                              # 本文件 - Claude Code的项目上下文配置文件说明
├── CLAUDE.md                              # 项目主规范 (入口)
├── PROJECT_CONFIG.ai-agents-platform.md   # 项目特定配置
├── PROJECT_CONFIG.template.md             # 项目配置模板
└── rules/                                 # 专题规范文档
    ├── architecture.md                    # CDK 架构规范 ★核心
    ├── project-structure.md               # 项目目录结构规范
    ├── construct-design.md                # Construct 设计规范
    ├── security.md                        # 安全规范 (IAM)
    ├── testing.md                         # 测试规范 (TDD)
    ├── deployment.md                      # 部署规范
    └── cost-optimization.md               # 成本优化规范



  图片所示的Monorepo 结构概览在三个子项目中都存在，你的优化方案是什么？  


  如下是对/Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-agents-platform/frontend   
是前端子项目的Claude Code 上下文（context）管理的规范文件的作用说明。请根据这个文件的作用说明。检查这些文件的内容是否存在违反了单一职责原则，以及相应的优化方案
.claude/
├── README.md                              # 本文件 - 目录说明
├── CLAUDE.md                              # 项目主规范 (入口)
├── PROJECT_CONFIG.ai-agents-platform.md   # 项目特定配置
├── PROJECT_CONFIG.template.md             # 项目配置模板
└── rules/                                 # 专题规范文档
    ├── architecture.md                    # 架构规范 (FSD) ★核心
    ├── project-structure.md               # 项目目录结构规范
    ├── component-design.md                # 组件设计规范
    ├── state-management.md                # 状态管理规范
    ├── code-style.md                      # 代码风格规范
    ├── testing.md                         # 测试规范 (TDD)
    ├── security.md                        # 前端安全规范
    ├── performance.md                     # 性能优化规范
    └── accessibility.md                   # 无障碍规范



    /Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-agents-platform/frontend  我在这个目录下增加了tech-stack.md，请你在/Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-agents-platform/infra/.claude/README.md中更新这个文件，并为其提供职责定义说明

我新增了tech-stack.md 作为技术栈规范单一来源，根据单一职责原则的要求，分析分散在/Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-agents-platform/frontend下的技术栈相关的说明有哪些应该统一到tech-stack.md中


/Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-agents-platform/backend/.claude/rules/logging.md是后端子项目的Claude Code 上下文（context）管理的规范文件，结合Claude Code 上下文管理的最佳实践在不影响它的作用的情况下精简冗余信息


/Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-sol
ution/ai-agents-platform/frontend  我在这个目录下增加了tech-stack.md，请你在/Users/jinhuasu/Project_Workspace/An
ker-Projects/ml-platform-research/llm-platform-solution/ai-agents-platform/frontend/.claude/README.md中更新这个文  
，并为其提供职责定义说明，同时frontend有更新，README.md需要跟改目录更新后到信息保持一致 




请为：/Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-agents-  
  platform/backend下的markdown在文件的开头添加清晰简要的职责定义


/claude-md-improver 当前infra项目中Claude Code的上下文管理的markdown文件相互之间的引用是否存在循环引入，引入关系不明确的问题，请给出改进方案


claude-md-improver 当前ai-agents-platform monorepo项目，包含后端（backend）、前端（frontend）和基础设施（infra）子项目，我再为这个项目打造Claude Code上下文管理的规范，目前已经基本完成，结合Claude code上下文管理的最佳实践，你对目前上下管理的有什么优化建议

  当前ai-agents-platform monorepo项目，包含后端（backend）、前端（frontend）和基础设施（infra）子项目, 我分别为这些子项目提供了Claude Code上下文管理的规范。分析这些子项目中定义的规范条目是否符合它们各自领域的最佳实践
  
  这些规范文件的命名你有什么优化建议吗？以便各个子项目下的规范文件的名称具有更好的可读性和一致性。


当前ai-agents-platform monorepo项目，对后端（backend）子项目，我为这个项目打造Claude Code上下文管理的规范，目前已经完成，结合Claude code上下文管理的最佳实践，你对目前上下管理的有什么优化建议

当前ai-agents-platform monorepo项目，对基础设施（infra）子项目，我为这个项目打造Claude Code上下文管理的规范，目前已经完成，结合Claude code上下文管理的最佳实践，你对目前上下管理的有什么优化建议




可以，但是对于每个问题的优化方案，你需要一个问题一个问题处理，每个问题你需要先说明优化的依据，获得我的确认后再执行 
  - infra/.claude/project-config.template.md → 移动到 doc/templates/


分析这个前端frontend子项目： /Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-agents-platform/frontend下上下文管理的规范文件，
结合Claude Code 上下文管理的最佳实践在不影响它的作用的情况下分析是否存在冗余信息，是否存在各个规范文件不满足单一职责原则、职责重叠的问题


按照Claude Code上下文管理的机制，对于会自动加载到Claude Code context的规范文档，在规范文档中引用别的文档是否有必要？增加引入和不增加引用有什么优缺点？你的优化方案是什么，依据是什么

当前ai-agents-platform monorepo项目，包含后端（backend）、前端（frontend）和基础设施（infra）子项目，我为这个项目打造Claude Code上下文管理的规范，目前已经完成。context-guide.md作为对各个子项目下的规范大说明，请分析这个context-guide.md是否跟项目的真实情况一致




当前ai-agents-platform monorepo项目，包含后端（backend）、前端（frontend）和基础设施（infra）子项目，我为这个项目打造Claude Code上下文管理的规范，目前已经完成，我手动将context-guide.md、project-config.template.md移动了到相应子目录下的doc目录下，请分析这个移动是否带来信息不一致的问题


当前ai-agents-platform monorepo项目，包含后端（backend）、前端（frontend）和基础设施（infra）子项目，我为这个项目打造Claude Code上下文管理的规范，目前已经完成。如果我想把这样的项目上下文管理的规范，可以让更多的人和项目来使用，我应该如何现实这样的目标呢？


我想依托Claude Code/Claude Agent SDK和开源生态以及Amazon Bedrock AgentCore开发一个AI Agents平台
项目，用户可以使用这个平台创建解决各种场景的Agent应用，帮我定义这个项目的愿景、目标、Metric等，我想以这个为基础驱动这个项目等长期迭代


对于每个问题的优化方案，你需要一个问题一个问题处理，每个问题你需要先说明优化的依据，获得我的确认后再执行 


完成/Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/claude-context-temp
  lates/docs/project-strategy.md 中Phase 1: Foundation（基础）— v1.0的任务  


基于我当前这个项目的背景，帮我推荐适合这个项目的Claude Code 的Plugin或者是Skill 或者是MCP  Agent teams 


docs/strategy/improvement-plan.md 相当于对/Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-agents-platform/docs中既存的progress.md和roadmap.md和其他文件的补充，类似真实产品研发中的需求或者优化的变更， 
  相当于软件产品研发过程中的变更，应该如何让Claude Code可以感知这种变更，并让现有的机制也能支持AI Agents Platform 这个项目支持真实情况下的迭代开发流程呢？    



审查一下目前这个项目的实现或者技术选型与方向是否符合 使用 Claude Agent SDK （https://platform.claude.com/docs/en/agent-sdk/overview）+ Claude Code Cli 来构建Agent应用，通过
AWS AgentCore Runtime解决该Agent应用的运行时，使用AWS AgentCore Gateway来对接外部MCP的统一入口，使用Amazon Bedrock Knowledge Base 作为Agent应用外接知识库，使用 AgentCore Observability Agent应用的观测性方案，使用使用 AgentCore Memory 管理Agent应用的Memory管理，并且当前的项目需要基于AWS AgentCore和Amazon Bedrock Knowledge Base提供的Python SDK来封装，请审查当前的技术方案是否符合这一要求。全面审查一下技术选型，启用Claude code agent teams 分配多个不同的agent进行全面分析

