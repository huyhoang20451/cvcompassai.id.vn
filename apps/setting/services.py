# Logic nghiệp vụ
from sqlmodel import Session
from .repository import (add_avatar_path_into_user as repo_add_avatar_path_into_user)
from fastapi import Depends, UploadFile
from fastapi.responses import JSONResponse
from typing import Annotated, List
from Core.Auth.schemas import user
from Core.Auth.dependencies import get_current_user
import os

async def upload_avatar(file: UploadFile, user_id: int, session: Session) -> str:

    AVATAR_DIR = "avatars"
    os.makedirs(AVATAR_DIR, exist_ok=True)

    try:
        file_ext = os.path.splitext(file.filename)[1]
        avatar_filename = f"user_{user_id}{file_ext}"
        avatar_path = os.path.join(AVATAR_DIR, avatar_filename)

        repo_add_avatar_path_into_user(session, user_id, avatar_path)
        # Đọc nội dung file
        content = await file.read()
        with open(avatar_path, "wb") as f:
            f.write(content)
        return avatar_path
    except Exception as e:
        raise RuntimeError(f"Lỗi khi upload CV: {e}")