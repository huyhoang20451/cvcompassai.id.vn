from sqlmodel import Session
from .repository import (get_jds_by_user_name as repo_get_jds_by_user_name,
                         add_jd as repo_add_jd,
                         get_cvs_by_jd_id as repo_get_cvs_by_jd_id,
                         get_jd_by_id as repo_get_jd_by_id,
                         delete_jd_by_id as repo_delete_jd_by_id,
                         update_jd_by_id as repo_update_jd_by_id,
                         update_business_by_id as repo_update_business_by_id,
                         get_job_categories as repo_get_job_categories,
                         get_cv_count_by_jd as repo_get_cv_count_by_jd,
                         get_total_cv_by_business_id as repo_get_total_cv_by_business_id,
                         get_total_jd_by_business_id as repo_get_total_jd_by_business_id)
from fastapi import Depends
from typing import Annotated, List
from .schemas import JD_create, JobCategory, jd_response, OCR_result, jd_CV
from Core.Auth.schemas import user
from Core.Auth.dependencies import get_current_user
from Core.OCR import compare

def get_jds_by_user_name(session: Session, username: str) -> List[jd_response]:
    return repo_get_jds_by_user_name(session, username)

def add_jd(session: Session, jd: JD_create) -> JD_create:
    return repo_add_jd(session, jd)

def OCR(image, JD: str) -> OCR_result:
    result = compare(image, JD)
    return OCR_result(**result)

def get_cvs_by_jd_id(session: Session, jd_id: int) -> List[jd_CV]:
    return repo_get_cvs_by_jd_id(session, jd_id)

import mimetypes

def detect_file_type(url: str):
    mime, _ = mimetypes.guess_type(url)
    if mime is None:
        return "unknown"
    elif mime.startswith("image/"):
        return "image"
    elif mime == "application/pdf":
        return "pdf"
    else:
        return "other"
    
def get_jd_by_id(session: Session, jd_id: int) -> str:
    jd = repo_get_jd_by_id(session, jd_id)
    parts = []
    if jd.job_description: parts.append(f"Mô tả công việc: {jd.job_description}")
    if jd.requirements: parts.append(f"Yêu cầu: {jd.requirements}")
    return "\n".join(parts)

def delete_jd_by_id(session: Session, jd_id: int, user_id: int) -> bool:
    return repo_delete_jd_by_id(session, jd_id, user_id)

def update_jd_by_id(session: Session, jd_id: int, new_jd: dict) -> bool:
    return repo_update_jd_by_id(session, jd_id, new_jd)

def update_business_by_id(session: Session, business_id: int, new_business: dict) -> bool:
    return repo_update_business_by_id(session, business_id, new_business)

def get_job_categories(session: Session) -> List[JobCategory]:
    return repo_get_job_categories(session)

def get_cv_count_by_jd(session: Session) -> dict:
    return repo_get_cv_count_by_jd(session)

def get_total_cv_by_business_id(session: Session, business_id: int) -> int:
    return repo_get_total_cv_by_business_id(session, business_id)

def get_total_jd_by_business_id(session: Session, business_id: int) -> int:
    return repo_get_total_jd_by_business_id(session, business_id)