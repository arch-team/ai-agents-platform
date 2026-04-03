# AI Agents Platform — 常用开发命令
# 用法: make <target> [ENV=dev|prod]

ENV ?= dev
# 项目固定部署在 us-east-1，覆盖环境变量中可能不同的 AWS_REGION
AWS_REGION := us-east-1
ECR_REGISTRY := 897473508751.dkr.ecr.$(AWS_REGION).amazonaws.com
ECR_REPO := ai-agents-platform-agent-$(ENV)
IMAGE_URI := $(ECR_REGISTRY)/$(ECR_REPO):latest
# AgentCore Runtime 要求 arm64 架构
IMAGE_PLATFORM := linux/arm64

# ============================================================
# Agent Runtime 镜像 (AgentCore Runtime 部署用)
# ============================================================

.PHONY: agent-build agent-push agent-deploy agent-status

## 构建 Agent Runtime 镜像 (arm64)
agent-build:
	cd backend && docker build -f Dockerfile.agent -t $(IMAGE_URI) --platform $(IMAGE_PLATFORM) .

## 推送到 ECR (需先 make ecr-login)
agent-push: agent-build
	docker push $(IMAGE_URI)

## 构建 + 推送 + 更新 Runtime (一键部署)
agent-deploy: ecr-login agent-push
	@echo ">>> 更新 AgentCore Runtime..."
	@STACK="ai-agents-plat-agentcore-$(ENV)"; \
	RUNTIME_ARN=$$(aws cloudformation describe-stacks --stack-name "$$STACK" \
		--query "Stacks[0].Outputs[?OutputKey=='RuntimeArn'].OutputValue" --output text --region $(AWS_REGION)); \
	RUNTIME_ID=$$(echo "$$RUNTIME_ARN" | sed 's|.*runtime/||'); \
	CONFIG=$$(aws bedrock-agentcore-control get-agent-runtime --agent-runtime-id "$$RUNTIME_ID" --region $(AWS_REGION)); \
	ROLE_ARN=$$(echo "$$CONFIG" | python3 -c "import json,sys; print(json.load(sys.stdin)['roleArn'])"); \
	NET_CFG=$$(echo "$$CONFIG" | python3 -c "import json,sys; print(json.dumps(json.load(sys.stdin)['networkConfiguration']))"); \
	aws bedrock-agentcore-control update-agent-runtime \
		--agent-runtime-id "$$RUNTIME_ID" \
		--agent-runtime-artifact "{\"containerConfiguration\":{\"containerUri\":\"$(IMAGE_URI)\"}}" \
		--role-arn "$$ROLE_ARN" \
		--network-configuration "$$NET_CFG" \
		--description "Local deploy ($(ENV))" \
		--region $(AWS_REGION); \
	echo ">>> Runtime $$RUNTIME_ID 更新中，等待就绪..."; \
	for i in $$(seq 1 12); do \
		STATUS=$$(aws bedrock-agentcore-control get-agent-runtime --agent-runtime-id "$$RUNTIME_ID" \
			--query 'status' --output text --region $(AWS_REGION)); \
		echo "  $$STATUS ($$i/12)"; \
		[ "$$STATUS" = "READY" ] && echo ">>> Runtime 就绪 ✅" && exit 0; \
		sleep 10; \
	done; \
	echo ">>> 超时，请手动检查"

## 查看 Runtime 状态
agent-status:
	@STACK="ai-agents-plat-agentcore-$(ENV)"; \
	RUNTIME_ARN=$$(aws cloudformation describe-stacks --stack-name "$$STACK" \
		--query "Stacks[0].Outputs[?OutputKey=='RuntimeArn'].OutputValue" --output text --region $(AWS_REGION)); \
	RUNTIME_ID=$$(echo "$$RUNTIME_ARN" | sed 's|.*runtime/||'); \
	aws bedrock-agentcore-control get-agent-runtime --agent-runtime-id "$$RUNTIME_ID" --region $(AWS_REGION) \
		--query "{id:agentRuntimeId,status:status,version:agentRuntimeVersion,updated:lastUpdatedAt}" --output table

# ============================================================
# SDK 管理
# ============================================================

.PHONY: sdk-upgrade sdk-version

## 升级 Claude Agent SDK 到最新版本
sdk-upgrade:
	cd backend && uv lock --upgrade-package claude-agent-sdk && uv sync
	@echo ">>> SDK 版本:"; cd backend && uv run python -c "import claude_agent_sdk; print(claude_agent_sdk.__version__)"

## 查看当前 SDK 版本
sdk-version:
	@cd backend && uv run python -c "import claude_agent_sdk; print(claude_agent_sdk.__version__)"

# ============================================================
# 通用
# ============================================================

.PHONY: ecr-login help

## 登录 ECR
ecr-login:
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(ECR_REGISTRY)

## 显示帮助
help:
	@echo "AI Agents Platform 开发命令"
	@echo ""
	@echo "Agent Runtime 镜像:"
	@echo "  make agent-build          构建 arm64 镜像"
	@echo "  make agent-push           构建 + 推送 ECR"
	@echo "  make agent-deploy         构建 + 推送 + 更新 Runtime (一键)"
	@echo "  make agent-deploy ENV=prod  Prod 环境一键部署"
	@echo "  make agent-status         查看 Runtime 状态"
	@echo ""
	@echo "SDK 管理:"
	@echo "  make sdk-upgrade          升级 SDK 到最新"
	@echo "  make sdk-version          查看当前版本"
	@echo ""
	@echo "通用:"
	@echo "  make ecr-login            登录 ECR"
