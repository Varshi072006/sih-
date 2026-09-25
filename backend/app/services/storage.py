from fastapi import HTTPException, UploadFile
from pathlib import Path
import secrets
import uuid

from app.config import settings
from app.models import StoredFile
from app.utils.constants import ALLOWED_MIME


def save_upload(
    db,
    file: UploadFile,
    uploaded_by: int | None,
    entity_type: str,
    entity_id: str,
    public: bool = False,
) -> StoredFile:
    content_type = file.content_type or "application/octet-stream"
    suffix = Path(file.filename or "file.bin").suffix.lower()
    allowed_exts = ALLOWED_MIME.get(content_type)
    if not allowed_exts or suffix not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"File type not allowed: {content_type} {suffix}")
    data = file.file.read()
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(status_code=400, detail=f"File exceeds {settings.MAX_UPLOAD_MB} MB limit")
    upload_root = Path(settings.UPLOAD_DIR)
    upload_root.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}_{secrets.token_hex(4)}{suffix}"
    path = upload_root / stored_name
    path.write_bytes(data)
    rec = StoredFile(
        filename=stored_name,
        original_name=file.filename or stored_name,
        file_type=content_type,
        size=len(data),
        uploaded_by=uploaded_by,
        entity_type=entity_type,
        entity_id=str(entity_id),
        storage_path=str(path),
        public=public,
    )
    db.add(rec)
    db.flush()
    return rec
