# CI/CD 部署配置指南

> 本文档说明如何配置 GitHub Environments、Secrets 和 AWS IAM OIDC，以支持 `cdk-deploy.yml` 工作流的 staging/production 部署。

---

## 1. GitHub Environments 配置

在仓库 **Settings > Environments** 中创建以下环境:

### 1.1 `dev` 环境

- 无特殊保护规则
- push 到 `main` / `ai-agents-factory-v1` 时自动触发部署

### 1.2 `staging` 环境

- **部署分支限制**: 仅允许 `main` 和 `ai-agents-factory-v1`
- dev 部署成功后自动触发

### 1.3 `production` 环境

- **Required reviewers**: 至少 1 名审批人 (建议 2 名)
- **部署分支限制**: 仅允许 `main` 和 `ai-agents-factory-v1`
- **Wait timer** (可选): 部署前等待 5 分钟，留出取消窗口
- staging 部署成功后触发，需审批通过后执行

---

## 2. GitHub Secrets 配置

在仓库 **Settings > Secrets and variables > Actions** 中配置:

| Secret 名称 | 作用域 | 说明 |
|-------------|--------|------|
| `AWS_ROLE_ARN` | Repository | Dev 环境 + CDK Diff 使用的 IAM Role ARN |
| `AWS_STAGING_ROLE_ARN` | Repository | Staging 环境部署使用的 IAM Role ARN |
| `AWS_PROD_ROLE_ARN` | Repository | Production 环境部署使用的 IAM Role ARN |

ARN 格式: `arn:aws:iam::<ACCOUNT_ID>:role/<ROLE_NAME>`

> 建议为每个环境使用独立 AWS 账号 (AWS Organizations)，通过不同 Role 隔离权限。

---

## 3. AWS IAM OIDC Provider 配置

GitHub Actions 通过 OIDC 获取临时凭证访问 AWS，无需存储长期密钥。

### 3.1 创建 OIDC Identity Provider

在每个目标 AWS 账号的 IAM 控制台执行:

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

或通过 CloudFormation/CDK:

```yaml
# CloudFormation 示例
GitHubOIDCProvider:
  Type: AWS::IAM::OIDCProvider
  Properties:
    Url: https://token.actions.githubusercontent.com
    ClientIdList:
      - sts.amazonaws.com
    ThumbprintList:
      - 6938fd4d98bab03faadb97b34396831e3780aea1
```

### 3.2 创建 IAM Role (每个环境)

信任策略 (Trust Policy):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:<GITHUB_ORG>/<REPO_NAME>:environment:<ENV_NAME>"
        }
      }
    }
  ]
}
```

将 `<ACCOUNT_ID>`、`<GITHUB_ORG>/<REPO_NAME>`、`<ENV_NAME>` 替换为实际值。

`<ENV_NAME>` 对应:
- dev 环境: `dev`
- staging 环境: `staging`
- production 环境: `production`

### 3.3 IAM Role 权限策略

Role 需要以下权限用于 CDK 部署:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws:iam::<ACCOUNT_ID>:role/cdk-*"
    }
  ]
}
```

> CDK Bootstrap 会创建 `cdk-*` 角色。确保已在目标账号执行 `cdk bootstrap`。

---

## 4. 首次部署验证

### 4.1 前置条件检查

```bash
# 1. 确认 CDK Bootstrap 已执行 (每个目标账号 + Region)
cd infra
pnpm cdk bootstrap aws://<ACCOUNT_ID>/ap-northeast-1

# 2. 确认 OIDC Provider 已创建
aws iam list-open-id-connect-providers

# 3. 确认 IAM Role 存在且信任策略正确
aws iam get-role --role-name <ROLE_NAME> --query 'Role.AssumeRolePolicyDocument'
```

### 4.2 验证流程

1. **CDK Diff (PR)**: 创建 PR 修改 `infra/` 目录，确认 CDK Diff job 正常运行并评论变更
2. **Dev 部署**: 合并 PR 到 main，确认 dev 部署 job 自动触发并成功
3. **Staging 部署**: 确认 dev 成功后 staging 自动触发并成功
4. **Prod 部署**: 确认 staging 成功后 prod job 等待审批，审批后部署成功

### 4.3 故障排查

| 症状 | 可能原因 | 解决方案 |
|------|---------|---------|
| `Not authorized to perform sts:AssumeRoleWithWebIdentity` | OIDC Provider 未创建或信任策略中 `sub` 条件不匹配 | 检查 GitHub org/repo 名称、environment 名称是否一致 |
| `CDK Bootstrap version mismatch` | 目标账号未执行 bootstrap 或版本过低 | 重新执行 `cdk bootstrap` |
| `Staging/Prod Role ARN not found` | Secret 名称拼写错误 | 检查 `AWS_STAGING_ROLE_ARN` / `AWS_PROD_ROLE_ARN` |
| Prod 部署未等待审批 | `production` environment 未配置 required_reviewers | 在 GitHub Settings > Environments 中配置 |

---

## 5. 部署流水线概览

```
push to main/ai-agents-factory-v1 (infra/** 变更)
  |
  v
[test] lint + typecheck + test + cdk synth
  |
  v
[deploy-dev] → AWS Dev 账号 (自动)
  |
  v
[deploy-staging] → AWS Staging 账号 (自动)
  |
  v
[deploy-prod] → AWS Prod 账号 (需审批)
```

PR 流程:
```
pull_request (infra/** 变更)
  |
  v
[test] lint + typecheck + test + cdk synth
  |
  v
[cdk-diff] → PR 评论 CDK 变更内容
```
