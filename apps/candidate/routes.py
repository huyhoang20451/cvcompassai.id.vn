# Chứa API
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Cookie, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from sqlmodel import Session
from .services import (search_jobs, 
                       get_cvs_by_username as service_get_cvs_by_username, 
                       get_jds, 
                       update_coin,
                       get_jd_by_id,
                       upload_cv,
                       get_candidate_cv_by_id,
                       add_cv_into_jd,
                       add_cv_into_candidate,
                       get_top_10_jds_by_cv)
from db import get_session
from Core.Auth.schemas import user
from .schemas import JobResponse, JobSearchRequest, candidate_CV
from Core.Auth.dependencies import templates, get_current_user, decode_token, authorize_role
from Core.OCR import run_vintern

router = APIRouter(tags=["candidate"])


# Home sau khi log in
@router.get("/home-logged-in", response_class=HTMLResponse)
async def home(request: Request, 
               user_info: user = Depends(authorize_role(["candidate"])), 
               session: Session = Depends(get_session)):
    # Tìm kiếm job theo từ khóa và vị trí
    keyword = request.query_params.get("keyword", "")
    location = request.query_params.get("location", "")
    if keyword or location:
        search_params = JobSearchRequest(keyword=keyword if keyword else None, location=location if location else None)
        job_descriptions = search_jobs(session, search_params)
    else:
        job_descriptions = get_jds(session)
    user_avatar = getattr(user_info, "avatar_path", None)
    return templates.TemplateResponse("home_logged_in.html", {"request": request, "job_descriptions": job_descriptions, "username": user_info.username, "user_avatar": user_avatar})

@router.get("/aboutus-logged-in", response_class=HTMLResponse)
async def about_us(request: Request,
                   user_info: user = Depends(authorize_role(["candidate"]))):
    return templates.TemplateResponse("aboutus-logged-in.html", {"request": request, "username": user_info.username})

@router.get("/pricing-user-logged-in", response_class=HTMLResponse)
async def pricing(request: Request,
                  user_info: user = Depends(authorize_role(["candidate"]))):
    return templates.TemplateResponse("pricing-user-logged-in.html", {"request": request, "username": user_info.username})

@router.get("/ocr-scan-logged-in", response_class=HTMLResponse)
async def ocr_scan(request: Request,
                   user_info: user = Depends(authorize_role(["candidate"]))):
    return templates.TemplateResponse("ocr-scan.html", {"request": request, "username": user_info.username})

@router.get("/finding-jobs", response_class=HTMLResponse)
async def finding_jobs(request: Request,
                       user_info: user = Depends(authorize_role(["candidate"]))):
    return templates.TemplateResponse("finding-jobs.html", {"request": request, "username": user_info.username, "user": user_info})

# Thanh tìm kiếm job
@router.post("/jobs_search", response_model=list[JobResponse])
async def jobs_search_endpoint(search_params: JobSearchRequest, 
                      session: Session = Depends(get_session)):
    """Endpoint wrapper that calls the candidate.services.search_jobs function.

    Renamed to avoid shadowing the imported `search_jobs` service.
    """
    try:
        jobs = search_jobs(session, search_params)
        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")

# Màn hình chi tiết JD
@router.get("/job-detail/{job_id}", response_class=HTMLResponse)
def job_detail(request: Request,
               job_id: int,
               user_info: user = Depends(authorize_role(["candidate"])),
               session: Session = Depends(get_session)):
    jd = get_jd_by_id(session, job_id)
    if not jd:
        raise HTTPException(status_code=404, detail="Job not found")
    return templates.TemplateResponse("job-detail.html", {"request": request, "job": jd, "username": user_info.username})

# Lấy tất cả CVs theo username lấy từ token
@router.get("/get_cvs", response_model= List[candidate_CV])
async def get_cvs_by_username(user_info: user = Depends(authorize_role(["candidate"])),
                              session: Session = Depends(get_session)):
    return service_get_cvs_by_username(user_info.username, session)

# Trừ coin vào database
@router.get("/deduct-coin")
async def deduct_coin(amount: int, user_info: user = Depends(authorize_role(["candidate"])), session: Session = Depends(get_session)):
    coin = user_info.coin
    if coin < amount:
        return JSONResponse(content={"success": False, "msg": "Bạn không đủ coin."})
    new_coin = coin - amount
    update_coin(session, user_info.username, new_coin)
    return JSONResponse(content={"success": True, "coin": new_coin})

# Lấy số coin trong database
@router.get("/get-coin")
async def get_coin(user_info: user = Depends(authorize_role(["candidate"]))):
    coin = user_info.coin
    return JSONResponse(content={"success": True, "coin": coin})

@router.get("/create-free-cv", response_class=HTMLResponse)
async def create_free_cv(request: Request, 
                   user_info: user = Depends(authorize_role(["candidate"]))):
    return templates.TemplateResponse("create-free-cv.html", {"request": request})

@router.get("/mycv-settings", response_class=HTMLResponse)
async def mycv_settings(request: Request,
                  user_info: user = Depends(authorize_role(["candidate"]))):
    return templates.TemplateResponse("mycv-settings.html", {"request": request, "username": user_info.username, "user": user_info})

@router.get("/finding-jobs", response_class=HTMLResponse)
async def finding_jobs(request: Request,
                       user_info: user = Depends(authorize_role(["candidate"]))):
    return templates.TemplateResponse("finding-jobs.html", {"request": request, "username": user_info.username, "user": user_info})

@router.post("/upload", response_class=HTMLResponse)
async def upload(request: Request,
                 file: UploadFile = File(...),
                 user_info: user = Depends(authorize_role(["candidate"])),
                 session: Session = Depends(get_session)):
    file_path = await upload_cv(file, user_info.id, session)
    if file.content_type == "application/pdf" or file.filename.lower().endswith(".pdf"):
        from Core.OCR import scan_pdf  # hàm đọc PDF
        result = scan_pdf(file_path)
    elif file.content_type.startswith("image/") or file.filename.lower().endswith((".jpg", ".jpeg", ".png")):
        from Core.OCR import run_vintern  # hàm OCR
        result = run_vintern(file_path)
    else:
        result = "File không hỗ trợ"

    return templates.TemplateResponse("ocr-scan.html", {"request": request, "result": result})

# Nộp cv cho jd bằng cv có sẵn trong database
@router.post("/submit-existing-cv", response_class=HTMLResponse)
async def submit_cv(request: Request,
                    jd_id: int,
                    existing_cv_id: Optional[int] = Form(None),
                    user_info: user = Depends(authorize_role(["candidate"])),
                    session: Session = Depends(get_session)):
    cv = get_candidate_cv_by_id(session, existing_cv_id) # Lấy cv trong bảng candidate_cv
    URL = cv.URL
    cv = add_cv_into_jd(session, URL, jd_id) # Add cv vào bảng jd_CV

    return templates.TemplateResponse("finding-jobs.html",{"request": request, 
                                                           "username": user_info.username})

# Nộp cv cho jd bằng cv upload từ máy
@router.post("/submit-upload-cv", response_class=HTMLResponse)
async def submit_cv(request: Request,
                    jd_id: int,
                    new_cv: Optional[UploadFile] = File(None),   # nếu upload CV mới
                    user_info: user = Depends(authorize_role(["candidate"])),
                    session: Session = Depends(get_session)):
    if not new_cv:
        raise HTTPException(status_code=400, detail="Chưa upload file")
    file_path = await upload_cv(new_cv, user_info.id, session) # Lưu cv về server và database bảng candidate_cv
    cv = add_cv_into_jd(session, file_path, jd_id) # Add cv vào bảng jd_CV

    return templates.TemplateResponse("finding-jobs.html",{"request": request, 
                                                           "username": user_info.username})

# Lọc top 10 jd theo cv
@router.get("/top10-best-jd", response_class=HTMLResponse)
def compare_cv_vs_jd(request: Request,
                     cv_id: int, 
                     user_info: user = Depends(authorize_role(["candidate"])),
                     session: Session = Depends(get_session)):
    top_10 = get_top_10_jds_by_cv(session, cv_id)
    return templates.TemplateResponse("compare_cv_vs_jd.html", {"request": request, "top_10": top_10})

# API để update coin cho user
@router.post("/api/update-coin")
async def api_update_coin(request: Request,
                         new_coin: int = Form(...),
                         user_info: user = Depends(authorize_role(["candidate"])),
                         session: Session = Depends(get_session)):
    """API để cập nhật coin cho user"""
    try:
        updated_coin = update_coin(session, user_info.username, new_coin)
        if updated_coin is not None:
            return {"success": True, "message": "Cập nhật coin thành công", "new_coin": updated_coin}
        else:
            return {"success": False, "message": "Không tìm thấy user"}
    except Exception as e:
        return {"success": False, "message": f"Lỗi: {str(e)}"}

# API để get coin từ database cho user
@router.get("/api/get-coin-db")
async def api_get_coin_db(user_info: user = Depends(authorize_role(["candidate"])),
                         session: Session = Depends(get_session)):
    """API để lấy coin từ database"""
    try:
        from .repository import get_user_by_username
        
        user_db = get_user_by_username(session, user_info.username)
        if user_db:
            coin = user_db.coin or 0
            return {"success": True, "coin": coin}
        else:
            return {"success": False, "msg": "Không tìm thấy người dùng.", "coin": 0}
    except Exception as e:
        return {"success": False, "msg": f"Lỗi: {str(e)}", "coin": 0}