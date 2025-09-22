# Chứa API
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session
from .services import (get_jds_by_user_name, 
                       add_jd, 
                       OCR, 
                       get_cvs_by_jd_id, 
                       detect_file_type,
                       get_jd_by_id)
from db import get_session
from Core.Auth.dependencies import templates, authorize_role
from Core.Auth.schemas import user
from .schemas import JD_form
from datetime import datetime, timezone
from typing import Optional
from Core.OCR import compare
router = APIRouter(tags=["business"])

@router.get("/business-home", response_class=HTMLResponse)
async def business_home(request: Request):
    return templates.TemplateResponse("home-business.html", {"request": request})

@router.get("/business-dashboard", response_class=HTMLResponse)
async def business_dashboard(request: Request,
                             user_info: user = Depends(authorize_role(["business"]))):
    print(user_info.company_name)
    return templates.TemplateResponse("business_dashboard.html", {"request": request, "username": user_info.username, "company": user_info.company_name})

@router.get("/pricing-business-logged-in", response_class=HTMLResponse)
async def pricing_business_logged_in(request: Request, 
                                     user_info: user = Depends(authorize_role(["business"]))):
    return templates.TemplateResponse("pricing_business_logged_in.html", {"request": request, "username": user_info.username, "company": user_info.company_name})

@router.get("/job-storage", response_class=HTMLResponse)
async def job_storage(request: Request,
                      jd_id: Optional[int] = None,
                      user_info: user = Depends(authorize_role(["business"])),
                      session : Session = Depends(get_session)):
    job_descriptions = get_jds_by_user_name(session, user_info.username)
    job = next((jd for jd in job_descriptions if jd.id == jd_id), None)

    return templates.TemplateResponse("job-storage.html", 
                                      {"request": request,
                                       "job_position": job_descriptions,
                                       "job": job,
                                       "username": user_info.username,
                                       "role": user_info.role,
                                       "company": user_info.company_name})

@router.post("/submit-job", response_class=HTMLResponse)
async def submit_job(request: Request, 
                     user_info: user = Depends(authorize_role(["business"])),
                     session: Session = Depends(get_session)):
    form = await request.form()
    jd_form = dict(form)
    jd_form["business_id"] = user_info.id
    jd_form["created_at"] = datetime.now(timezone.utc)
    jd_form = JD_form(**jd_form)
    jd = add_jd(session, jd_form)
    return RedirectResponse(url=f"/job-storage?company={user_info.company_name}&username={user_info.username}", status_code=303)

@router.get("/dang-tuyen-ngay", response_class=HTMLResponse)
def dang_tuyen_ngay(request: Request, 
                    user_info: user = Depends(authorize_role(["business"]))):
    return templates.TemplateResponse("form-dang-tuyen-ngay.html", {"request": request, 
                                                                    "username": user_info.username, 
                                                                    "company": user_info.company_name})

@router.get("/cv-detail-business", response_class=HTMLResponse)
def cv_detail_business(request: Request, 
                       user_info: user = Depends(authorize_role(["business"]))):
    return templates.TemplateResponse("cv-detail-business.html", {"request": request, 
                                                                  "username": user_info.username, 
                                                                  "company": user_info.company_name})

@router.get("/compare_cv_vs_jd", response_class=HTMLResponse)
def compare_cv_vs_jd(request: Request,
                     jd_id: int, 
                     user_info: user = Depends(authorize_role(["business"])),
                     session: Session = Depends(get_session)):
    cvs = get_cvs_by_jd_id(session, jd_id)
    jd = get_jd_by_id(session, jd_id)
    results = []
    for cv in cvs:
        file_type = detect_file_type(cv.URL)
        comparison = compare(cv.URL, jd, file_type)
        results.append({"cv_url": cv.URL,
                        "met": comparison.get("Met", []),
                        "not_met": comparison.get("Not_Met", [])})
    print(results)
    return templates.TemplateResponse("cv-detail-business.html", {"request": request,
                                                                  "username": user_info.username,
                                                                  "company": user_info.company_name,
                                                                  "results": results})
