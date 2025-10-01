# Truy vấn cơ sỏ dữ liệu
from sqlmodel import Session, select
from models import User_db, jd_db, candidate_CV_db, jd_CV_db
from .schemas import candidate_CV, jd, jd_CV
from sqlalchemy import or_
from typing import List, Optional

# Lấy tất cả JD theo keyword và location trong database
def search_jobs(session: Session, 
                keyword: str = None, 
                location: str = None) -> List[jd]:
    statement = (
        select(jd_db, User_db.avatar_path)
        .join(User_db, jd_db.business_id == User_db.id)
    )

    if keyword:
        keyword_pattern = f"%{keyword}%"
        statement = statement.where(
            or_(
                jd_db.title.ilike(keyword_pattern),
                jd_db.job_description.ilike(keyword_pattern)  # dùng đúng tên cột
            )
        )
    if location:
        location_pattern = f"%{location}%"
        statement = statement.where(jd_db.location.ilike(location_pattern))

    results = session.exec(statement).all()

    jobs = []
    for jd_in_db, avatar_path in results:
        job = jd.model_validate(jd_in_db, from_attributes=True)
        job.avatar_path = avatar_path
        jobs.append(job)

    return jobs

# Lấy tất cả CV theo username trong database
def get_cvs_by_username(session: Session, 
            username: str) -> List[candidate_CV]:
    statement = (   
        select(candidate_CV_db)
        .join(User_db, candidate_CV_db.user_id == User_db.id)
        .where(User_db.username == username)
    )
    results = session.exec(statement).all()
    CVs = [candidate_CV.model_validate(cv) for cv in results] # Chuyển sang Pydantic model
    return CVs

# Lấy tất cả JD trong database
def get_jds(session: Session) -> List[jd]:
    statement = (
        select(jd_db, User_db.avatar_path)
        .join(User_db, jd_db.business_id == User_db.id)
    )
    results = session.exec(statement).all()

    jds = []
    for jd_in_db, avatar_path in results:
        jd_obj = jd.model_validate(jd_in_db, from_attributes=True)
        jd_obj.avatar_path = avatar_path
        jds.append(jd_obj)

    return jds

def get_jd_by_id(session: Session, id: int) -> jd:
    statement = (
        select(jd_db, User_db.avatar_path)
        .join(User_db, jd_db.business_id == User_db.id)
        .where(jd_db.id == id)
    )
    result = session.exec(statement).first()
    if result:
        jd_in_db, avatar_path = result
        jd_obj = jd.model_validate(jd_in_db, from_attributes=True)
        jd_obj.avatar_path = avatar_path
        return jd_obj
    return None

# Cập nhật coin mới vào database
def update_coin(session: Session, 
                username: str, 
                new_coin: int) -> Optional[int]:

    statement = select(User_db).where(User_db.username == username)
    result = session.exec(statement).first()

    if result is None:
        return None  # không tìm thấy user

    # Update coin
    result.coin = new_coin
    session.add(result)
    session.commit()
    session.refresh(result)

    return result.coin

def get_candidate_cv_by_id(session: Session, cv_id:int) -> candidate_CV:
    cv = session.exec(select(candidate_CV_db).where(candidate_CV_db.cv_id == cv_id)).first()
    return candidate_CV.model_validate(cv)

def add_cv_into_jd(session: Session, URL: str, jd_id: int) -> jd_CV:
    db_obj = jd_CV_db(URL=URL, jd_id=jd_id)

    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)  # để lấy id vừa tạo
    
    return jd_CV.model_validate(db_obj)

def add_cv_into_candidate(session: Session, URL: str, user_id: int) -> candidate_CV:
    db_obj = candidate_CV_db(URL=URL, user_id=user_id)

    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)  # để lấy id vừa tạo
    
    return candidate_CV.model_validate(db_obj)

def get_cvs_by_id(session: Session, cv_id: int) -> candidate_CV:
    statement = (select(candidate_CV_db).where(candidate_CV_db.id == cv_id))
    result = session.exec(statement).first()
    if result:
        return candidate_CV.model_validate(result)
    return None