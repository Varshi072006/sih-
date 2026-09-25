from sqlalchemy.orm import Session

from app.models import Notification, User


class NotificationService:
    @staticmethod
    def notify_user(
        db: Session,
        recipient_id: int,
        notification_type: str,
        title: str,
        message: str,
        entity_type: str = "",
        entity_id: str = "",
    ) -> Notification:
        rec = Notification(
            recipient_id=recipient_id,
            notification_type=notification_type,
            title=title,
            message=message,
            entity_type=entity_type,
            entity_id=str(entity_id),
        )
        db.add(rec)
        db.flush()
        return rec

    @staticmethod
    def notify_role(
        db: Session,
        role: str,
        notification_type: str,
        title: str,
        message: str,
        entity_type: str = "",
        entity_id: str = "",
    ) -> int:
        users = db.query(User).filter(User.primary_role == role, User.is_active.is_(True)).all()
        for u in users:
            NotificationService.notify_user(
                db, u.id, notification_type, title, message, entity_type, entity_id
            )
        return len(users)

    @staticmethod
    def notify_department(db: Session, department_id: int, **kwargs) -> int:
        from app.models import GovernmentUser

        officers = db.query(GovernmentUser).filter(GovernmentUser.department_id == department_id).all()
        for o in officers:
            NotificationService.notify_user(db, o.user_id, **kwargs)
        return len(officers)

    @staticmethod
    def notify_university(db: Session, university_id: int, **kwargs) -> None:
        from app.models import University

        uni = db.get(University, university_id)
        if uni:
            NotificationService.notify_user(db, uni.user_id, **kwargs)

    @staticmethod
    def notify_industry(db: Session, industry_id: int, **kwargs) -> None:
        from app.models import Industry

        org = db.get(Industry, industry_id)
        if org:
            NotificationService.notify_user(db, org.user_id, **kwargs)
