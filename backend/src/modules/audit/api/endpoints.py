"""审计日志 API 端点 — 仅 ADMIN 角色可访问。"""

import csv
import io
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from src.modules.audit.api.dependencies import get_audit_service
from src.modules.audit.api.schemas.responses import (
    AuditLogListResponse,
    AuditLogResponse,
    AuditStatsResponse,
)
from src.modules.audit.application.dto.audit_log_dto import AuditLogDTO
from src.modules.audit.application.services.audit_service import AuditService
from src.modules.auth.api.dependencies import require_role
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.auth.domain.value_objects.role import Role
from src.shared.api.schemas import calc_total_pages


router = APIRouter(prefix="/api/v1/audit-logs", tags=["audit"])

# 类型别名
ServiceDep = Annotated[AuditService, Depends(get_audit_service)]
AdminDep = Annotated[UserDTO, Depends(require_role(Role.ADMIN))]


def _to_response(dto: AuditLogDTO) -> AuditLogResponse:
    """将 DTO 转换为 API 响应。"""
    return AuditLogResponse(
        id=dto.id,
        actor_id=dto.actor_id,
        actor_name=dto.actor_name,
        action=dto.action,
        category=dto.category,
        resource_type=dto.resource_type,
        resource_id=dto.resource_id,
        resource_name=dto.resource_name,
        module=dto.module,
        ip_address=dto.ip_address,
        user_agent=dto.user_agent,
        request_method=dto.request_method,
        request_path=dto.request_path,
        status_code=dto.status_code,
        result=dto.result,
        error_message=dto.error_message,
        details=dto.details,
        occurred_at=dto.occurred_at,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
    )


@router.get("")
async def list_audit_logs(
    service: ServiceDep,
    _admin: AdminDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    category: str | None = None,
    action: str | None = None,
    actor_id: int | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> AuditLogListResponse:
    """获取审计日志列表（分页 + 筛选）。"""
    from datetime import datetime

    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None

    paged = await service.list_filtered(
        page=page,
        page_size=page_size,
        category=category,
        action=action,
        actor_id=actor_id,
        resource_type=resource_type,
        resource_id=resource_id,
        start_date=start_dt,
        end_date=end_dt,
    )
    return AuditLogListResponse(
        items=[_to_response(item) for item in paged.items],
        total=paged.total,
        page=paged.page,
        page_size=paged.page_size,
        total_pages=calc_total_pages(paged.total, page_size),
    )


@router.get("/stats")
async def get_audit_stats(
    service: ServiceDep,
    _admin: AdminDep,
    start_date: str | None = None,
    end_date: str | None = None,
) -> AuditStatsResponse:
    """获取审计统计信息。"""
    from datetime import datetime

    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None

    stats = await service.get_stats(start_date=start_dt, end_date=end_dt)
    return AuditStatsResponse(
        by_category=stats.by_category,
        by_action=stats.by_action,
        total=stats.total,
    )


@router.get("/resource/{resource_type}/{resource_id}")
async def get_audit_logs_by_resource(
    resource_type: str,
    resource_id: str,
    service: ServiceDep,
    _admin: AdminDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> AuditLogListResponse:
    """按资源查询审计日志。"""
    paged = await service.get_by_resource(
        resource_type=resource_type,
        resource_id=resource_id,
        page=page,
        page_size=page_size,
    )
    return AuditLogListResponse(
        items=[_to_response(item) for item in paged.items],
        total=paged.total,
        page=paged.page,
        page_size=paged.page_size,
        total_pages=calc_total_pages(paged.total, page_size),
    )


@router.get("/export")
async def export_audit_logs(
    service: ServiceDep,
    _admin: AdminDep,
    category: str | None = None,
    action: str | None = None,
    actor_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    max_rows: Annotated[int, Query(ge=1, le=100000)] = 10000,
) -> StreamingResponse:
    """导出审计日志为 CSV 文件。"""
    from datetime import datetime

    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None

    paged = await service.list_filtered(
        page=1,
        page_size=max_rows,
        category=category,
        action=action,
        actor_id=actor_id,
        start_date=start_dt,
        end_date=end_dt,
    )

    # 生成 CSV 内容
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "actor_id", "actor_name", "action", "category",
        "resource_type", "resource_id", "resource_name", "module",
        "ip_address", "request_method", "request_path", "status_code",
        "result", "error_message", "occurred_at",
    ])
    for item in paged.items:
        writer.writerow([
            item.id, item.actor_id, item.actor_name, item.action, item.category,
            item.resource_type, item.resource_id, item.resource_name, item.module,
            item.ip_address, item.request_method, item.request_path, item.status_code,
            item.result, item.error_message, item.occurred_at.isoformat(),
        ])

    csv_bytes = output.getvalue().encode("utf-8-sig")
    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_logs.csv"},
    )


@router.get("/{audit_log_id}")
async def get_audit_log(
    audit_log_id: int,
    service: ServiceDep,
    _admin: AdminDep,
) -> AuditLogResponse:
    """获取单条审计日志详情。"""
    dto = await service.get_by_id(audit_log_id)
    return _to_response(dto)
