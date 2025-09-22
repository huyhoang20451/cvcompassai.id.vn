from sqlmodel import Session, select
from models import User_db, jd_db, jd_CV_db, candidate_CV_db
from .schemas import JD_form, jd_CV, candidate_CV
from typing import List

def get_jds_by_user_name(session: Session, username: str) -> List[JD_form]:
    statement = (
        select(jd_db)
        .join(User_db, jd_db.business_id == User_db.id)
        .where(User_db.username == username)
    )
    results = session.exec(statement).all()
    jds = [JD_form.model_validate(jd_in_db) for jd_in_db in results]
    return jds

def get_user_by_jd_id(session: Session, jd_id: int) -> User_db:
    statement = (
        select(User_db)
        .join(jd_db, jd_db.business_id == User_db.id)
        .where(jd_db.id == jd_id)
    )
    result = session.exec(statement).first()
    return result

def add_jd(session: Session, jd: JD_form) -> JD_form:
    db_obj  = jd_db(**jd.model_dump())  # Pydantic v2 -> dùng model_dump()
    
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)  # để lấy id vừa tạo
    
    return JD_form.model_validate(db_obj)

def get_cvs_by_jd_id(session: Session, jd_id: int) -> List[jd_CV]:
    statement = (select(jd_CV_db).where(jd_CV_db.jd_id == jd_id))
    results = session.exec(statement).all()
    cvs = [jd_CV.model_validate(cv_in_db) for cv_in_db in results]
    return cvs

def get_jd_by_id(session: Session, jd_id: int) -> JD_form:
    jd = session.exec(select(jd_db).where(jd_db.id == jd_id)).first()
    return jd


