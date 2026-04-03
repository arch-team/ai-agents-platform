"""启动时 seed 数据和恢复逻辑。"""

from __future__ import annotations

from src.shared.infrastructure.settings import get_settings


async def seed_default_admin() -> None:
    """启动时同步默认管理员账户（upsert: 不存在则创建，存在则同步密码和状态）。

    Secrets Manager 中的 DEFAULT_ADMIN_PASSWORD 是 Source of Truth。
    每次启动时验证 DB 中的密码哈希是否匹配，不匹配则更新，同时解除账户锁定。
    """
    import structlog

    from src.modules.auth.application.services.password_service import hash_password, verify_password
    from src.modules.auth.domain.entities.user import User
    from src.modules.auth.infrastructure.persistence.repositories.user_repository_impl import UserRepositoryImpl
    from src.shared.domain.value_objects.role import Role
    from src.shared.infrastructure.database import get_session_factory

    log = structlog.get_logger(__name__)
    settings = get_settings()
    session_factory = get_session_factory()

    admin_pwd = settings.DEFAULT_ADMIN_PASSWORD.get_secret_value()
    if not admin_pwd:
        log.info("default_admin_skip", reason="DEFAULT_ADMIN_PASSWORD 未配置, 跳过默认管理员同步")
        return

    async with session_factory() as session:
        try:
            repo = UserRepositoryImpl(session=session)
            existing = await repo.get_by_email(settings.DEFAULT_ADMIN_EMAIL)

            if existing is None:
                admin = User(
                    email=settings.DEFAULT_ADMIN_EMAIL,
                    hashed_password=hash_password(admin_pwd),
                    name=settings.DEFAULT_ADMIN_NAME,
                    role=Role.ADMIN,
                )
                created = await repo.create(admin)
                await session.commit()
                log.info("default_admin_created", user_id=created.id, email=settings.DEFAULT_ADMIN_EMAIL)
                return

            synced_fields: list[str] = []

            if not verify_password(admin_pwd, existing.hashed_password):
                existing.hashed_password = hash_password(admin_pwd)
                synced_fields.append("password")

            if existing.is_locked or existing.failed_login_count > 0:
                existing.reset_failed_logins()
                synced_fields.append("unlock")

            # 确保管理员角色和激活状态
            if existing.role != Role.ADMIN:
                existing.role = Role.ADMIN
                synced_fields.append("role")
            if not existing.is_active:
                existing.is_active = True
                synced_fields.append("activate")

            if synced_fields:
                await repo.update(existing)
                await session.commit()
                log.info("default_admin_synced", email=settings.DEFAULT_ADMIN_EMAIL, synced=synced_fields)
            else:
                log.info("default_admin_ok", email=settings.DEFAULT_ADMIN_EMAIL)

        except Exception:
            await session.rollback()
            log.exception("default_admin_seed_failed")


async def seed_default_templates() -> None:
    """启动时 seed 预置模板（幂等：已存在则同步 config，不存在则创建）。"""
    import structlog

    from src.modules.auth.infrastructure.persistence.repositories.user_repository_impl import UserRepositoryImpl
    from src.modules.templates.application.dto.template_dto import CreateTemplateDTO
    from src.modules.templates.application.services.template_service import TemplateService
    from src.modules.templates.domain.seed_data import SEED_TEMPLATES
    from src.modules.templates.domain.value_objects.template_config import TemplateConfig
    from src.modules.templates.infrastructure.persistence.repositories.template_repository_impl import (
        TemplateRepositoryImpl,
    )
    from src.shared.infrastructure.database import get_session_factory

    log = structlog.get_logger(__name__)
    settings = get_settings()
    session_factory = get_session_factory()

    async with session_factory() as session:
        try:
            # 查询 Admin 用户作为模板创建者
            user_repo = UserRepositoryImpl(session=session)
            admin = await user_repo.get_by_email(settings.DEFAULT_ADMIN_EMAIL)
            if admin is None or admin.id is None:
                log.warning("default_templates_seed_skipped_no_admin")
                return

            template_repo = TemplateRepositoryImpl(session=session)
            service = TemplateService(template_repo=template_repo)

            seeded = 0
            synced = 0
            for tpl_raw in SEED_TEMPLATES:
                tpl: dict[str, object] = tpl_raw
                name = str(tpl["name"])
                seed_model_id = str(tpl["model_id"])
                seed_temperature = float(str(tpl["temperature"]))
                seed_max_tokens = int(str(tpl["max_tokens"]))

                existing = await template_repo.get_by_name(name)
                if existing is not None:
                    # upsert: 同步 model_id / temperature / max_tokens, 防止模型升级后 DB 滞后
                    cfg = existing.config
                    if (
                        cfg.model_id != seed_model_id
                        or cfg.temperature != seed_temperature
                        or cfg.max_tokens != seed_max_tokens
                    ):
                        existing.config = TemplateConfig(
                            system_prompt=cfg.system_prompt,
                            model_id=seed_model_id,
                            temperature=seed_temperature,
                            max_tokens=seed_max_tokens,
                            tool_ids=list(cfg.tool_ids),
                            knowledge_base_ids=list(cfg.knowledge_base_ids),
                        )
                        existing.touch()
                        await template_repo.update(existing)
                        synced += 1
                    continue

                dto = CreateTemplateDTO(
                    name=name,
                    description=str(tpl["description"]),
                    category=str(tpl["category"]),
                    system_prompt=str(tpl["system_prompt"]),
                    model_id=seed_model_id,
                    temperature=seed_temperature,
                    max_tokens=seed_max_tokens,
                    tags=[str(t) for t in list(tpl["tags"])],  # type: ignore[call-overload]
                )
                created_dto = await service.create_template(dto, current_user_id=admin.id)

                # 将模板发布为可用状态
                await service.publish_template(created_dto.id, current_user_id=admin.id)

                # 同步 is_featured 字段: create_template 不接收该字段, 直接更新 entity
                if tpl.get("is_featured"):
                    created_template = await template_repo.get_by_id(created_dto.id)
                    if created_template is not None:
                        created_template.is_featured = True
                        await template_repo.update(created_template)

                seeded += 1

            if seeded > 0 or synced > 0:
                await session.commit()
                log.info("default_templates_seeded", created=seeded, synced=synced)
            else:
                log.info("default_templates_already_exist")
        except Exception:
            await session.rollback()
            log.exception("default_templates_seed_failed")


async def recover_zombie_executions() -> None:
    """启动时将 RUNNING/PENDING 的团队执行标记为 FAILED（ECS 重启恢复）。"""
    import structlog

    from src.modules.execution.domain.value_objects.team_execution_status import TeamExecutionStatus
    from src.modules.execution.infrastructure.persistence.repositories.team_execution_repository_impl import (
        TeamExecutionRepositoryImpl,
    )
    from src.shared.infrastructure.database import get_session_factory

    log = structlog.get_logger(__name__)
    session_factory = get_session_factory()

    async with session_factory() as session:
        try:
            repo = TeamExecutionRepositoryImpl(session=session)
            zombies = await repo.list_by_statuses(
                [TeamExecutionStatus.PENDING, TeamExecutionStatus.RUNNING],
            )
            if not zombies:
                return

            for execution in zombies:
                if execution.status == TeamExecutionStatus.PENDING:
                    execution.start()
                execution.fail("服务重启, 执行中断")
                await repo.update(execution)

            await session.commit()
            log.info("zombie_executions_recovered", count=len(zombies))
        except Exception:
            await session.rollback()
            log.exception("zombie_executions_recovery_failed")
