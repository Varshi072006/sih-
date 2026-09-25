from sqlalchemy.orm import Session

from app.models import AuditLog, User


class AuditLogService:
    @staticmethod
    def log(
        db: Session,
        action: str,
        entity_type: str,
        entity_id: str,
        user: User | None = None,
        previous_status: str = "",
        new_status: str = "",
        details: str = "",
        ip_address: str = "",
        user_agent: str = "",
    ) -> AuditLog:
        rec = AuditLog(
            user_id=user.id if user else None,
            role=user.primary_role if user else "",
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            previous_status=previous_status,
            new_status=new_status,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(rec)
        db.flush()
        return rec
