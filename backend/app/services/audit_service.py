from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.enums import UserRole
from app.models.user import User


async def write_audit(
    db: AsyncSession,
    actor: User,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    details: str | None = None,
) -> None:
    log = AuditLog(
        actor_id=actor.id,
        actor_role=UserRole(actor.role.value),
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    )
    db.add(log)
