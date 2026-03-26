---
id: otel-console-exporter-floods-cloudwatch
trigger: "when configuring OpenTelemetry tracing in dev/ECS environment"
confidence: 0.9
domain: "observability"
source: "session-observation-2026-02-28"
---

# OTel ConsoleSpanExporter 淹没 CloudWatch 日志

## Action
Dev 环境无 OTLP 端点时，使用 NoOpSpanExporter 而非 ConsoleSpanExporter。

## Evidence
- 2026-02-28: CloudWatch 日志被 OTel Span JSON 完全淹没，500 条日志全是 Span 数据
- structlog 业务日志 (info/warning/error) 不可见，无法诊断问题
- 替换为 _NoOpSpanExporter 后日志立即清晰可读

## Pattern
ConsoleSpanExporter 将每个 Span 的完整 JSON 输出到 stdout → 与 structlog JSON 混杂 → CloudWatch 解析器失败
