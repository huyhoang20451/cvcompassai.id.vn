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

    # Lưu avatar trong folder `static/avatars` để có thể phục vụ trực tiếp
    AVATAR_DIR = os.path.join("static", "avatars")
    os.makedirs(AVATAR_DIR, exist_ok=True)

    try:
        file_ext = os.path.splitext(file.filename)[1]
        avatar_filename = f"user_{user_id}{file_ext}"
        avatar_fs_path = os.path.join(AVATAR_DIR, avatar_filename)

        # Đọc nội dung file và ghi vào filesystem
        content = await file.read()
        with open(avatar_fs_path, "wb") as f:
            f.write(content)

        # Trả về đường dẫn public (được serve từ /static)
        avatar_url = f"/static/avatars/{avatar_filename}"

        # Lưu đường dẫn public vào DB
        repo_add_avatar_path_into_user(session, user_id, avatar_url)

        return avatar_url
    except Exception as e:
        raise RuntimeError(f"Lỗi khi upload CV: {e}")