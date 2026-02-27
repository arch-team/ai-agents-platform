# ============================================================
# 多阶段构建: builder (依赖安装) + runtime (最小运行时)
# Build: 2026-02-19 (ProcessError graceful handling)
# ============================================================

# -- Stage 1: Builder --
FROM public.ecr.aws/docker/library/python:3.12-slim AS builder

# 安装构建依赖 (asyncmy 需要 gcc 编译 Cython 扩展)
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev && rm -rf /var/lib/apt/lists/*

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# 先复制依赖定义, 利用 Docker 缓存
COPY pyproject.toml uv.lock* ./

# 安装生产依赖 (不含 dev 依赖)
# claude-agent-sdk 的 Linux x86_64 wheel 自带 bundled CLI (Node.js SEA 编译的 ELF 二进制)
# 不需要在容器中安装 Node.js 或 npm
RUN uv sync --no-dev --frozen --no-install-project

# 复制源码和构建所需文件
COPY scripts/ scripts/
COPY src/ src/
COPY migrations/ migrations/
COPY alembic.ini .
COPY README.md .

# 安装项目本身
RUN uv sync --no-dev --frozen

# -- Stage 2: Runtime --
FROM public.ecr.aws/docker/library/python:3.12-slim AS runtime

# Claude Agent SDK bundled CLI (Node.js SEA ELF 二进制) 运行时依赖
# python:3.12-slim 缺少 libstdc++6 等, 导致 CLI 进程启动后立即崩溃 (ProcessTransport not ready)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libstdc++6 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 安全: 非 root 用户运行
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --create-home appuser

WORKDIR /app

# 从 builder 复制虚拟环境和源码
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
COPY --from=builder /app/migrations /app/migrations
COPY --from=builder /app/alembic.ini /app/alembic.ini
COPY --from=builder /app/scripts /app/scripts

# 设置 PATH 使用虚拟环境
# CLAUDE_CODE_USE_BEDROCK: 启用 Bedrock 认证路径 (IAM Role → Bedrock Invoke API)
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CLAUDE_CODE_USE_BEDROCK=1

# 切换到非 root 用户
USER appuser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; r = httpx.get('http://localhost:8000/health'); r.raise_for_status()"

# 启动命令: Alembic 迁移 + Uvicorn
CMD ["sh", "-c", "python scripts/migrate_with_lock.py && uvicorn src.presentation.api.main:app --host 0.0.0.0 --port 8000"]
