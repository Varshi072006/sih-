from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import StoredFile, User
from app.security.deps import get_current_user, get_optional_user, is_gov
from app.utils.constants import ADMIN_ROLES

router = APIRouter(prefix="/api/files", tags=["Files"])


@router.get("/{file_id}")
def get_file(file_id: int, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    rec = db.get(StoredFile, file_id)
    if not rec:
        raise HTTPException(status_code=404, detail="File not found")
    if not rec.public:
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")
        if user.primary_role not in ADMIN_ROLES and not is_gov(user) and rec.uploaded_by != user.id:
            raise HTTPException(status_code=403, detail="You cannot access this file")
    path = Path(rec.storage_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Stored file missing")
    return FileResponse(path, filename=rec.original_name, media_type=rec.file_type)
