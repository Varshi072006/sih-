from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import Message, Notification, User
from app.schemas import MessageIn
from app.security.deps import get_current_user
from app.services.notifications import NotificationService
from app.utils.constants import ADMIN_ROLES, GOVERNMENT_ROLES, INDUSTRY_ROLES, UNIVERSITY_ROLES

router = APIRouter(prefix="/api", tags=["Communication"])

ALLOWED = {
    "citizen": GOVERNMENT_ROLES | ADMIN_ROLES,
    "government_officer": {"citizen"} | UNIVERSITY_ROLES | INDUSTRY_ROLES | ADMIN_ROLES | GOVERNMENT_ROLES,
    "government_department": {"citizen"} | UNIVERSITY_ROLES | INDUSTRY_ROLES | ADMIN_ROLES,
    "university": GOVERNMENT_ROLES | INDUSTRY_ROLES | ADMIN_ROLES | UNIVERSITY_ROLES,
    "faculty": GOVERNMENT_ROLES | INDUSTRY_ROLES | ADMIN_ROLES,
    "student": GOVERNMENT_ROLES | ADMIN_ROLES,
    "industry": GOVERNMENT_ROLES | UNIVERSITY_ROLES | ADMIN_ROLES | INDUSTRY_ROLES,
    "startup": GOVERNMENT_ROLES | UNIVERSITY_ROLES | ADMIN_ROLES,
    "msme": GOVERNMENT_ROLES | UNIVERSITY_ROLES | ADMIN_ROLES,
    "csr": GOVERNMENT_ROLES | UNIVERSITY_ROLES | ADMIN_ROLES,
    "admin": set(),
    "super_admin": set(),
}


def _can_message(sender: User, recipient: User) -> bool:
    if sender.primary_role in ADMIN_ROLES or recipient.primary_role in ADMIN_ROLES:
        return True
    allowed = ALLOWED.get(sender.primary_role, set())
    return recipient.primary_role in allowed


@router.get("/notifications")
def list_notifications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = (
        db.query(Notification)
        .filter(Notification.recipient_id == user.id)
        .order_by(Notification.id.desc())
        .limit(100)
        .all()
    )
    return [
        {
            "id": n.id,
            "type": n.notification_type,
            "title": n.title,
            "message": n.message,
            "entity_type": n.entity_type,
            "entity_id": n.entity_id,
            "read": n.read,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in items
    ]


@router.post("/notifications/{nid}/read")
def read_notification(nid: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    n = db.get(Notification, nid)
    if not n or n.recipient_id != user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.read = True
    db.commit()
    return {"read": True}


@router.get("/messages")
def messages(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = (
        db.query(Message)
        .filter((Message.sender_id == user.id) | (Message.recipient_id == user.id))
        .order_by(Message.id.desc())
        .limit(200)
        .all()
    )
    return [
        {
            "id": m.id,
            "sender_id": m.sender_id,
            "recipient_id": m.recipient_id,
            "subject": m.subject,
            "body": m.body,
            "read": m.read,
            "problem_id": m.problem_id,
            "project_id": m.project_id,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in items
    ]


@router.post("/messages")
def send_message(payload: MessageIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    recipient = db.get(User, payload.recipient_id)
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    if not _can_message(user, recipient):
        raise HTTPException(status_code=403, detail="This conversation is not permitted for your role")
    rec = Message(
        sender_id=user.id,
        recipient_id=recipient.id,
        subject=payload.subject,
        body=payload.body,
        problem_id=payload.problem_id,
        project_id=payload.project_id,
    )
    db.add(rec)
    NotificationService.notify_user(
        db, recipient.id, "message", payload.subject or "New message", payload.body[:200], "message", ""
    )
    db.commit()
    return {"id": rec.id}
