# Truy vấn cơ sỏ dữ liệu
from sqlmodel import Session, select
from models import User_db, jd_db, candidate_CV_db, jd_CV_db
from .schemas import user
from sqlalchemy import or_
from typing import List, Optional

def add_avatar_path_into_user(session: Session, user_id: int, avatar_path: str) -> user:
    db_obj = session.get(User_db, user_id)  # Lấy user từ DB
    if not db_obj:
        raise ValueError(f"User với id={user_id} không tồn tại")
    db_obj.avatar_path = avatar_path  # cập nhật field avatar
    session.add(db_obj)               # không bắt buộc vì db_obj đã nằm trong session
    session.commit()
    session.refresh(db_obj)

    return user.model_validate(db_obj)