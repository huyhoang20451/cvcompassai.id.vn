from sqlmodel import Session, func, select
from models import JobCategory_db, SavedJob, User_db, jd_db, jd_CV_db, candidate_CV_db
from .schemas import JD_create, JobCategory, jd_response, jd_CV, candidate_CV
from typing import List

def get_jds_by_user_name(session: Session, username: str) -> List[jd_response]:
    # 1️⃣ Lấy danh sách JD của user
    statement = (
        select(jd_db, User_db.company_name, User_db.avatar_path)
        .join(User_db, jd_db.business_id == User_db.id)
        .where(User_db.username == username)
    )
    jd_results = session.exec(statement).all()

    # 2️⃣ Lấy số lượng CV theo JD (trả về dạng dict: {jd_id: cv_count})
    cv_statement = (
        select(jd_CV_db.jd_id, func.count(jd_CV_db.id))
        .group_by(jd_CV_db.jd_id)
    )
    cv_results = session.exec(cv_statement).all()
    cv_count_map = {jd_id: count for jd_id, count in cv_results}

    # 3️⃣ Gộp hai kết quả lại
    return [
        jd_response.model_validate({
            **jd.model_dump(),
            "company_name": company_name,
            "avatar_path": avatar_path,
            "cv_count": cv_count_map.get(jd.id, 0)
        })
        for jd, company_name, avatar_path in jd_results
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

# Xóa JD, chỉ được xóa bởi chính user tạo ra nó
def delete_jd_by_id(session: Session, jd_id: int, user_id: int) -> bool:
    jd = session.exec(
        select(jd_db).where(jd_db.id == jd_id, jd_db.business_id == user_id)
    ).first()
    if not jd:
        return False
    session.delete(jd)
    session.commit()
    return True

def update_jd_by_id(session: Session, jd_id: int, new_jd: dict) -> bool:
    statement = select(jd_db).where(jd_db.id == jd_id)
    existing_jd = session.exec(statement).first()

    if not existing_jd:
        return False
    
    for key, value in new_jd.items():
        setattr(existing_jd, key, value)

    session.commit()
    session.refresh(existing_jd)
    return True

def update_business_by_id(session: Session, business_id: int, new_business: dict) -> bool:
    result = session.exec(select(User_db).where(User_db.id == business_id)).first()
    if not result:
        return False
    for key, value in new_business.items():
        setattr(result, key, value)
    session.add(result)
    session.commit()
    session.refresh(result)
    return True

def get_job_categories(session: Session):
    statement = select(JobCategory_db)
    results = session.exec(statement).all()
    return [JobCategory.model_validate(job_category) for job_category in results]


def get_total_cv_by_business_id(session: Session, business_id: int):
    """
    Lấy tổng số CV của tất cả các job thuộc business_id cụ thể.
    """
    statement = (
        select(func.count(jd_CV_db.id).label("num_of_cv"))
        .join(jd_db, jd_db.id == jd_CV_db.jd_id)
        .where(jd_db.business_id == business_id)
    )
    result = session.exec(statement).first()
    return result or 0

def get_total_jd_by_business_id(session: Session, business_id: int):
    """
    Lấy tổng số JD (tin tuyển dụng) thuộc về business_id cụ thể.
    """
    statement = (
        select(func.count(jd_db.id).label("num_of_jd"))
        .where(jd_db.business_id == business_id)
    )
    result = session.exec(statement).first()
    return result or 0

def approve_cv(session: Session, id: int, approval: bool) -> bool:
    jd_cv = session.exec(
        select(jd_CV_db).where(jd_CV_db.id == id)
    ).first()
    if not jd_cv:
        return False
    jd_cv.approved = approval
    session.add(jd_cv)
    session.commit()
    session.refresh(jd_cv)
    return True

def count_approved_cv_by_company(session: Session, company_id: int) -> int:
    """
    Đếm số lượng CV đã được approved=True cho một công ty cụ thể.
    """
    result = session.exec(
        select(func.count()).where(
            (jd_CV_db.company_id == company_id) &
            (jd_CV_db.approved == True)
        )
    ).one()
    return result

def count_saved_jobs_by_company(session: Session, company_id: int) -> int:
    count = session.exec(
        select(func.count()).where(SavedJob.company_id == company_id)
    ).one()
    return count