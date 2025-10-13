from sqlmodel import Session, select
from models import User_db, jd_db, jd_CV_db, candidate_CV_db
from .schemas import JD_create, jd_response, jd_CV, candidate_CV
from typing import List

def get_jds_by_user_name(session: Session, username: str) -> List[jd_response]:
    statement = (
        select(jd_db, User_db.username, User_db.company_name)
        .join(User_db, jd_db.business_id == User_db.id)
        .where(User_db.username == username)
    )
    results = session.exec(statement).all()
    return [
        jd_response.model_validate({**jd.model_dump(), "username": u, "company_name": c})
        for jd, u, c in results
    ]

def get_user_by_jd_id(session: Session, jd_id: int) -> User_db:
    statement = (
        select(User_db)
        .join(jd_db, jd_db.business_id == User_db.id)
        .where(jd_db.id == jd_id)
    )
    result = session.exec(statement).first()
    return result

def add_jd(session: Session, jd: JD_create) -> JD_create:
    db_obj  = jd_db(**jd.model_dump())  # Pydantic v2 -> dùng model_dump()
    
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)  # để lấy id vừa tạo
    
    return JD_create.model_validate(db_obj)

def get_cvs_by_jd_id(session: Session, jd_id: int) -> List[jd_CV]:
    statement = (select(jd_CV_db).where(jd_CV_db.jd_id == jd_id))
    results = session.exec(statement).all()
    cvs = [jd_CV.model_validate(cv_in_db) for cv_in_db in results]
    return cvs

def get_jd_by_id(session: Session, jd_id: int) -> jd_response:
    jd = session.exec(select(jd_db).where(jd_db.id == jd_id)).first()
    return jd

def get_jd_by_id(session: Session, jd_id: int) -> jd_response:
    statement = (
        select(
            jd_db,
            User_db.username,
            User_db.company_name,
        )
        .join(User_db, jd_db.business_id == User_db.id)
        .where(jd_db.id == jd_id)
    )
    result = session.exec(statement).first()
    if not result:
        return None

    jd_in_db, username, company_name = result
    jd_data = jd_in_db.model_dump()
    jd_data.update({"username": username, "company_name": company_name})
    return jd_response.model_validate(jd_data)
