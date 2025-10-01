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
                         get_cvs_by_id as repo_get_cvs_by_id)
from fastapi import Depends, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from typing import Annotated, List
from .schemas import JobSearchRequest, JobResponse, jd, candidate_CV, jd_CV
from Core.Auth.schemas import user
from Core.Auth.dependencies import get_current_user
from Core.OCR import compare_qwen
import os

def search_jobs(session: Session, 
                search_params: JobSearchRequest) -> list[JobResponse]:
    jobs = repo_search_jobs(session, 
                            search_params.keyword, 
                            search_params.location)
    return [JobResponse.model_validate(job) for job in jobs] # Chuyển sang Pydantic

def get_cvs_by_username(username: str, session: Session) -> List[candidate_CV]:
    return repo_get_cvs_by_username(session, 
                                    username)

def get_jds(session: Session) -> List[jd]:
    return repo_get_jds(session)

def update_coin (session: Session,
                 username: str,
                 coin: int) -> int:
    return repo_update_coin(session, username, coin)

def get_jd_by_id(session: Session, id: int) -> jd:
    return repo_get_jd_by_id(session, id)

def add_cv_into_candidate(session: Session, URL: str, user_id: int) -> candidate_CV:
    cv = repo_add_cv_into_candidate(session, URL, user_id)
    return cv

async def upload_cv(file: UploadFile, user_id: int, session: Session) -> str:

    UPLOAD_DIR = "cv"
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    try:
        file_location = os.path.join(UPLOAD_DIR, file.filename)
        add_cv_into_candidate(session, file_location, user_id)
        # Đọc nội dung file
        content = await file.read()
        with open(file_location, "wb") as f:
            f.write(content)
        return file_location
    except Exception as e:
        raise RuntimeError(f"Lỗi khi upload CV: {e}")

def get_candidate_cv_by_id(session: Session, cv_id: int) -> candidate_CV:
    cv = repo_get_candidate_cv_by_id(session, cv_id)
    return cv

def add_cv_into_jd(session: Session, URL: str, jd_id: int) -> jd_CV:
    cv = repo_add_cv_into_jd(session, URL, jd_id)
    return cv

def jd_to_str(jd: jd) -> str:
    """
    Convert job description fields into a full English text
    for CV matching / semantic comparison.
    """
    parts = [
        f"Job Title: {jd.title}" if jd.title else "",
        f"Company: {jd.company_name}" if jd.company_name else "",
        f"Industry: {jd.industry}" if jd.industry else "",
        f"Position Level: {jd.position}" if jd.position else "",
        f"Salary: {jd.salary}" if jd.salary else "",
        f"Location: {jd.location}" if jd.location else "",
        f"Workplace Type: {jd.workplace}" if jd.workplace else "",
        f"Job Description: {jd.job_description}" if jd.job_description else "",
        f"Requirements: {jd.requirements}" if jd.requirements else "",
        f"Benefits: {jd.benefits}" if jd.benefits else "",
        f"Working Time: {jd.working_time}" if jd.working_time else "",
        f"Application Deadline: {jd.deadline}" if jd.deadline else "",
    ]
    return "\n".join([p for p in parts if p])

def get_top_10_jds_by_cv(session: Session, cv_id: int) -> List[jd]:
    jds = repo_get_jds(session)
    cv = repo_get_cvs_by_id(session, cv_id)
    if not cv.details:
        raise HTTPException(
            status_code=400,
            detail="Bạn cần quét CV trước khi hệ thống gợi ý công việc."
        )
    cv_details = cv.details
    results = []
    for jd in jds:
        print(f"chuỗi JD: {jd_to_str(jd)}")
        print(f"chuỗi CV: {cv_details}")
        results.append({
            "jd": jd,
            "Ratio": compare_qwen(jd_to_str(jd), cv_details)["Ratio"]
        })

    top_10 = sorted(results, key=lambda x: x["Ratio"], reverse=True)[:10]
    return [r["jd"] for r in top_10]
