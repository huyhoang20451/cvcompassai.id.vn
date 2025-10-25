# Truy vấn cơ sỏ dữ liệu
from sqlmodel import Session, select
from models import JobCategory_db, User_db, jd_db, candidate_CV_db, jd_CV_db, SavedJob
from .schemas import candidate_CV, jd, jd_CV, JobCategory
from sqlalchemy import or_
from typing import List, Optional
from sqlalchemy import or_, and_

def get_user_by_username(session: Session, username: str) -> User_db:
    """Get user by username from database"""
    statement = select(User_db).where(User_db.username == username)
    result = session.exec(statement).first()
    return result

# Lấy tất cả JD theo keyword và các bộ lọc
def search_jobs(session: Session,
                job_categories: Optional[List[str]] = None, # danh sách ngành nghề
                min_filter: Optional[int] = None,  # mức lương tối thiểu
                max_filter: Optional[int] = None,  # mức lương tối đa
                keyword: Optional[str] = None,  # từ khóa
                sort_by: Optional[str] = "newest")-> List[jd]:
    # 1️⃣ Khởi tạo câu select cơ bản
    statement = (
        select(jd_db, User_db.avatar_path, User_db.company_name)
        .join(User_db, jd_db.business_id == User_db.id)
    )

    # 2️⃣ Bộ lọc điều kiện
    conditions = []

    if job_categories:
        conditions.append(jd_db.job_category.in_(job_categories))

    if min_filter:
        conditions.append(jd_db.min_salary >= min_filter)

    if max_filter:
        conditions.append(jd_db.max_salary <= max_filter)

    if keyword:
        keyword_like = f"%{keyword.lower()}%"
        conditions.append(
            or_(
                jd_db.title.ilike(keyword_like),
                jd_db.job_description.ilike(keyword_like),
                jd_db.requirements.ilike(keyword_like),
            )
        )

    if conditions:
        statement = statement.where(and_(*conditions))

    # 3️⃣ Sắp xếp
    if sort_by == "newest":
        statement = statement.order_by(jd_db.created_at.desc())
    elif sort_by == "highest_salary":
        statement = statement.order_by(jd_db.min_salary.desc())
    elif sort_by == "expiring_soon":
        statement = statement.order_by(jd_db.deadline.asc())

    results = session.exec(statement).all()

    return [
        jd.model_validate({**jd.model_dump(), "avatar_path": a, "company_name": c})
        for jd, a, c in results
    ]

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
        select(jd_db, 
               User_db.avatar_path,
               User_db.company_name)
        .join(User_db, jd_db.business_id == User_db.id)
    )
    results = session.exec(statement).all()

    jds = []
    for jd_in_db, avatar_path, company_name in results:
        jd_obj = jd.model_validate(jd_in_db, from_attributes=True)
        jd_obj.avatar_path = avatar_path
        jd_obj.company_name = company_name
        jds.append(jd_obj)

    return jds

def get_jd_by_id(session: Session, id: int) -> jd:
    statement = (
        select(jd_db, 
               User_db.avatar_path,
               User_db.company_name)
        .join(User_db, jd_db.business_id == User_db.id)
        .where(jd_db.id == id)
    )
    result = session.exec(statement).first()
    if result:
        jd_in_db, avatar_path, company_name = result
        jd_obj = jd.model_validate(jd_in_db, from_attributes=True)
        jd_obj.avatar_path = avatar_path
        jd_obj.company_name = company_name
        return jd_obj
    return None

# Cập nhật coin mới vào database
def update_coin(session: Session, 
                user_id: int, 
                new_coin: int) -> Optional[int]:

    statement = select(User_db).where(User_db.id == user_id)
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
    cv = session.exec(select(candidate_CV_db).where(candidate_CV_db.id == cv_id)).first()
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

def save_jd(session: Session, candidate_id: int, job_id: int):
    # Kiểm tra xem job đã được lưu chưa
    existing = session.exec(
        select(SavedJob)
        .where(SavedJob.candidate_id == candidate_id)
        .where(SavedJob.job_id == job_id)
    ).first()

    if existing:
        return None  # hoặc raise HTTPException nếu muốn báo lỗi

    # Tạo bản ghi mới
    saved_job = SavedJob(candidate_id=candidate_id, job_id=job_id)
    session.add(saved_job)
    session.commit()
    session.refresh(saved_job)  # cập nhật lại instance với id mới sinh ra

    return saved_job

def get_job_categories(session: Session):
    statement = select(JobCategory_db)
    results = session.exec(statement).all()
    return [JobCategory.model_validate(job_category) for job_category in results]

def get_saved_jobs_by_user(session: Session, user_id: int) -> List[jd]:
    """
    Lấy danh sách các công việc mà người dùng đã lưu,
    bao gồm thông tin chi tiết của job.
    """
    statement = (
        select(
            jd_db.title,
            jd_db.location,
            jd_db.min_salary,
            jd_db.max_salary,
            jd_db.position,
            jd_db.job_description,
            jd_db.requirements,
            jd_db.benefits,
            jd_db.working_time,
            jd_db.application_method,
        )
        .join(SavedJob, jd_db.id == SavedJob.job_id)
        .where(SavedJob.user_id == user_id)
    )
    results = session.exec(statement).all()
    return [jd.model_validate(result) for result in results]