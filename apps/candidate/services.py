# Logic nghiệp vụ
from sqlmodel import Session
from .repository import (search_jobs as repo_search_jobs,
                         get_cvs_by_username as repo_get_cvs_by_username,
                         get_jds as repo_get_jds,
                         update_coin as repo_update_coin,
                         get_jd_by_id as repo_get_jd_by_id,
                         get_candidate_cv_by_id as repo_get_candidate_cv_by_id,
                         add_cv_into_jd as repo_add_cv_into_jd,
                         add_cv_into_candidate as repo_add_cv_into_candidate,
                         get_cvs_by_id as repo_get_cvs_by_id,
                         save_jd as repo_save_jd,
                         get_job_categories as repo_get_job_categories,
                         get_saved_jobs_by_user as repo_get_saved_jobs_by_user,
                         update_candidate_cv as repo_update_candidate_cv,
                         get_cv_with_top10_jds as repo_get_cv_with_top10_jds,
                         get_applied_cvs as repo_get_applied_cvs,
                         get_jds_by_category as repo_get_jds_by_category)
from fastapi import Depends, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from typing import Annotated, List, Optional
from .schemas import JobCategory, JobSearchRequest, JobResponse, jd, candidate_CV, jd_CV
from Core.Auth.schemas import user
from Core.Auth.dependencies import get_current_user
from Core.OCR import compare_qwen
import os

def search_jobs(session: Session,
                job_categories: List[str] = None, # danh sách ngành nghề
                min_filter: int = None,  # mức lương tối thiểu
                max_filter: int = None,  # mức lương tối đa
                keyword: str = None,  # từ khóa
                sort_by: Optional[str] = "newest")-> List[jd]:
    jobs = repo_search_jobs(session,
                            job_categories=job_categories,
                            min_filter=min_filter,
                            max_filter=max_filter,
                            keyword=keyword,
                            sort_by=sort_by)
    return jobs

def get_cvs_by_username(username: str, session: Session) -> List[candidate_CV]:
    return repo_get_cvs_by_username(session, 
                                    username)

def get_jds(session: Session) -> List[jd]:
    return repo_get_jds(session)

def get_jds_by_category(session: Session, job_category: str) -> List[jd]:
    return repo_get_jds_by_category(session, job_category)

def update_coin (session: Session,
                 id: int,
                 coin: int) -> int:
    return repo_update_coin(session, id, coin)

def get_jd_by_id(session: Session, id: int) -> jd:
    return repo_get_jd_by_id(session, id)

def add_cv_into_candidate(session: Session, URL: str, user_id: int) -> candidate_CV:
    cv = repo_add_cv_into_candidate(session, URL, user_id)
    return cv

def update_candidate_cv(session: Session, cv_id: int, top10_jds: Optional[List[int]] = None, unlocked: Optional[bool] = None) -> candidate_CV:
    cv = repo_update_candidate_cv(session, cv_id, top10_jds=top10_jds, unlocked=unlocked)
    return cv

async def upload_cv(file: UploadFile, user_id: int, session: Session):

    UPLOAD_DIR = "cv"
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    try:
        file_location = os.path.join(UPLOAD_DIR, file.filename)
        cv = add_cv_into_candidate(session, file_location, user_id)
        # Đọc nội dung file
        content = await file.read()
        with open(file_location, "wb") as f:
            f.write(content)
        return file_location, cv
    except Exception as e:
        raise RuntimeError(f"Lỗi khi upload CV: {e}")

def get_candidate_cv_by_id(session: Session, cv_id: int) -> candidate_CV:
    cv = repo_get_candidate_cv_by_id(session, cv_id)
    return cv

def add_cv_into_jd(session: Session, URL: str, jd_id: int, candidate_id: int) -> jd_CV:
    jd = get_jd_by_id(session, jd_id)
    if not jd:
        raise HTTPException(status_code=404, detail="Job not found")
    business_id = jd.business_id
    cv = repo_add_cv_into_jd(session, URL, jd_id, candidate_id, business_id)
    return cv

def jd_to_str(jd: jd) -> str:
    """
    Convert job description fields into a full English text
    for CV matching / semantic comparison.
    """
    parts = [
        f"Job Title: {jd.title}" if jd.title else "",
        f"Category: {jd.job_category or jd.category}" if (jd.job_category or jd.category) else "",
        f"Position Level: {jd.position}" if jd.position else "",
        f"Company: {jd.company_name}" if jd.company_name else "",
        f"Location: {jd.location}" if jd.location else "",
        f"Workplace Type: {jd.workplace}" if jd.workplace else "",
        f"Minimum Salary: {jd.min_salary}" if jd.min_salary else "",
        f"Maximum Salary: {jd.max_salary}" if jd.max_salary else "",
        f"Job Description: {jd.job_description}" if jd.job_description else "",
        f"Requirements: {jd.requirements}" if jd.requirements else "",
        f"Benefits: {jd.benefits}" if jd.benefits else "",
        f"Working Time: {jd.working_time}" if jd.working_time else "",
    ]
    return "\n".join([p for p in parts if p])

def get_top_10_jds_by_cv(session: Session, cv: str) -> List[jd]:
    jds = repo_get_jds(session)

    results = []

    for jd in jds:
        try:
            result = compare_qwen(jd_to_str(jd), cv)
            ratio = result.get("Ratio", 0)
            print(f"✅ JD ID: {jd.id} | Ratio: {ratio}")
            results.append({"jd": jd, "Ratio": ratio})
        except Exception as e:
            print(f"❌ Lỗi khi xử lý JD ID {jd.id}: {e}")

    top_10 = sorted(results, key=lambda x: x["Ratio"], reverse=True)[:10]
    for r in top_10:
        print(r["jd"].dict())
    return [r["jd"] for r in top_10]

def save_jd(session: Session, candidate_id: int, job_id: int):
    jd = get_jd_by_id(session, job_id)
    if not jd:
        raise HTTPException(status_code=404, detail="Job not found")
    business_id = jd.business_id
    jd = repo_save_jd(session, candidate_id, job_id, business_id)
    return jd

def get_job_categories(session: Session) -> List[JobCategory]:
    return repo_get_job_categories(session)

def get_saved_jobs_by_user(session: Session, user_id: int) -> List[jd]:
    return repo_get_saved_jobs_by_user(session, user_id)

def get_cv_with_top10_jds(session: Session, cv_id: int) -> Optional[candidate_CV]:
    return repo_get_cv_with_top10_jds(session, cv_id)

def get_cvs_with_top10_jds(username: str, session: Session) -> List[candidate_CV]:
    cvs = repo_get_cvs_by_username(session, username)
    result_cvs = []
    for cv in cvs:
        cv_with_jds = get_cv_with_top10_jds(session, cv.id)
        if cv_with_jds:
            result_cvs.append(cv_with_jds)
    return result_cvs

def get_applied_cvs(session: Session, candidate_id: int):
    return repo_get_applied_cvs(session, candidate_id)