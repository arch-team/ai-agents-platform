## EVAL: cdk-infrastructure
Created: 2026-02-21

### Capability Evals

#### NetworkStack (网络层)
- [ ] VPC 3 个可用区 (AZ)
- [ ] NAT Gateway 1 个 (成本优化)
- [ ] VPC Flow Log 启用
- [ ] S3 VPC Endpoint 配置
- [ ] 公有/私有子网正确划分

#### SecurityStack (安全层)
- [ ] KMS 加密密钥创建
- [ ] API Security Group 配置正确
- [ ] Database Security Group 配置正确 (仅允许 API SG 入站)
- [ ] JWT Secret 存储在 Secrets Manager
- [ ] Prod 环境: SM VPC Endpoint 配置

#### DatabaseStack (数据库层)
- [ ] Aurora MySQL 3.10.0+ Serverless v2 集群
- [ ] Dev 环境: db.t3.medium 单实例
- [ ] Prod 环境: db.r6g.large Writer + Reader 双实例
- [ ] 自动备份启用 (保留天数合理)
- [ ] Prod Performance Insights 启用

#### AgentCoreStack (AgentCore 层)
- [ ] ECR 仓库创建 (Agent 镜像)
- [ ] AgentCore Runtime 部署 (2 AZ)
- [ ] AgentCore Gateway 配置 (MCP Target)
- [ ] Cognito User Pool 创建
- [ ] Cognito User Pool Client 配置

#### ComputeStack (计算层)
- [ ] ECS Fargate 集群创建
- [ ] ALB (Application Load Balancer) 配置
- [ ] Dev 环境: 256 CPU / 512 MiB / 1 任务
- [ ] Prod 环境: 512 CPU / 1024 MiB / 2 任务
- [ ] Health Check 路径配置 (/health)
- [ ] Dev 定时缩减: UTC 12:00 → 0 任务, UTC 00:00 → 1 任务 (C-S4-8)
- [ ] 环境变量注入正确 (DB 连接字符串、JWT Secret、Bedrock 配置)

#### MonitoringStack (监控层)
- [ ] CloudWatch Alarms 配置
- [ ] CloudWatch Dashboard 创建
- [ ] SNS 告警通知
- [ ] ECS 服务 CPU/内存告警阈值合理
- [ ] Aurora 连接数/CPU 告警阈值合理

#### Stack 命名规范
- [ ] 所有 Stack 命名: `ai-agents-plat-{stack}-{env}` (v1.4 规范化)
- [ ] Dev 环境 Stack 名正确
- [ ] Prod 环境 Stack 名正确

#### 环境差异
- [ ] Dev 和 Prod 通过 CDK Context (env) 区分
- [ ] 资源规格按环境正确配置
- [ ] Prod 有更高的可用性 (多任务、Reader 实例)
- [ ] Dev 有成本优化 (定时缩减)

#### 跨 Stack 依赖
- [ ] NetworkStack 输出: VPC, 子网 ID
- [ ] SecurityStack 输出: SG, KMS Key, JWT Secret ARN
- [ ] DatabaseStack 输出: Aurora 连接端点
- [ ] Stack 部署顺序: Network → Security → Database → AgentCore → Compute → Monitoring

#### S3 存储
- [ ] KnowledgeDocsBucket 创建 (知识库文档)
- [ ] S3 版本管理启用 (灾备)
- [ ] 生命周期策略合理

#### 灾备能力
- [ ] Aurora 自动备份 RPO < 5min
- [ ] 快照恢复脚本可执行
- [ ] S3 版本回滚脚本可执行
- [ ] RTO < 15min 目标

### Regression Evals

#### 快照测试
- [ ] 所有 6 个 Stack 快照测试通过
- [ ] 快照与当前 CDK 代码一致

#### 编译
- [ ] TypeScript 编译无错误
- [ ] CDK synth 成功生成 CloudFormation 模板

#### 安全
- [ ] 无公开的数据库端点
- [ ] 无不必要的入站规则
- [ ] KMS 加密启用

#### 兼容性
- [ ] CDK 版本与 @aws-cdk/aws-bedrock-agentcore-alpha 兼容
- [ ] Stack 更新不导致资源替换 (无意外的 Replace)

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals

### Test Commands
```bash
# CDK 编译
cd infra && npm run build

# 全量测试
cd infra && npm test

# 快照测试
cd infra && npx jest --testPathPattern=snapshot

# CDK synth 验证
cd infra && npx cdk synth --context env=dev --quiet
cd infra && npx cdk synth --context env=prod --quiet

# Lint 检查
cd infra && npx eslint .
```
