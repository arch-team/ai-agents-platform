# ============================================================
# 多阶段构建: builder (依赖安装) + runtime (最小运行时)
# ============================================================

# -- Stage 1: Builder --
FROM python:3.12-slim AS builder

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# 先复制依赖定义, 利用 Docker 缓存
COPY pyproject.toml uv.lock* ./

# 安装生产依赖 (不含 dev 依赖)
RUN uv sync --no-dev --frozen --no-install-project

# 复制源码
COPY src/ src/
COPY migrations/ migrations/
COPY alembic.ini .

# 安装项目本身
RUN uv sync --no-dev --frozen

# -- Stage 2: Runtime --
FROM python:3.12-slim AS runtime

# 安全: 非 root 用户运行
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --create-home appuser

WORKDIR /app

# 从 builder 复制虚拟环境和源码
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
COPY --from=builder /app/migrations /app/migrations
COPY --from=builder /app/alembic.ini /app/alembic.ini

# 设置 PATH 使用虚拟环境
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 切换到非 root 用户
USER appuser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; r = httpx.get('http://localhost:8000/health'); r.raise_for_status()"

# 启动命令: Alembic 迁移 + Uvicorn
CMD ["sh", "-c", "alembic upgrade head && uvicorn src.presentation.api.main:app --host 0.0.0.0 --port 8000"]
