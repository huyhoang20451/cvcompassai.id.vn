# Chứa API
from typing import Annotated, List, Optional
from urllib import request
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
                       get_top_10_jds_by_cv,
                       save_jd as service_save_jd,
                       get_job_categories)
from db import get_session
from Core.Auth.schemas import user
from .schemas import JobResponse, JobSearchRequest, candidate_CV, jd
from Core.Auth.dependencies import templates, get_current_user, decode_token, authorize_role
from Core.OCR import run_vintern

router = APIRouter(tags=["candidate"])


# Home sau khi log in
@router.get("/home-logged-in", response_class=HTMLResponse)
async def home(request: Request, 
               user_info: user = Depends(authorize_role(["candidate"])), 
               session: Session = Depends(get_session)):
    job_descriptions = get_jds(session)
    job_categories = get_job_categories(session)
    return templates.TemplateResponse("home_logged_in.html", {"request": request, 
                                                              "job_descriptions": job_descriptions, 
                                                              "user_info": user_info,
                                                              "job_categories": job_categories},
                                                              )

@router.get("/aboutus-logged-in", response_class=HTMLResponse)
async def about_us(request: Request,
                   user_info: user = Depends(authorize_role(["candidate"]))):
    return templates.TemplateResponse("aboutus-logged-in.html", {"request": request, 
                                                                 "user_info": user_info})

@router.get("/pricing-user-logged-in", response_class=HTMLResponse)
async def pricing(request: Request,
                  user_info: user = Depends(authorize_role(["candidate"]))):
    return templates.TemplateResponse("pricing-user-logged-in.html", {"request": request, 
                                                                      "user_info": user_info})

@router.get("/ocr-scan-logged-in", response_class=HTMLResponse)
async def ocr_scan(request: Request,
                   user_info: user = Depends(authorize_role(["candidate"]))):
    return templates.TemplateResponse("ocr-scan.html", {"request": request, 
                                                        "user_info": user_info})

@router.get("/finding-jobs", response_class=HTMLResponse)
async def finding_jobs(request: Request,
                       user_info: user = Depends(authorize_role(["candidate"])),
                       session: Session = Depends(get_session)):
    job_descriptions = get_jds(session)
    return templates.TemplateResponse("finding-jobs.html", {"request": request,
                                                            "user_info": user_info,
                                                            "job_descriptions": job_descriptions})

# Thanh tìm kiếm job theo từ khóa và filter
@router.post("/jobs_search", response_model=list[jd])
async def jobs_search_endpoint(request: Request,
                               job_categories: List[str] = None, # danh sách ngành nghề
                               min_filter: int = None,  # mức lương tối thiểu
                               max_filter: int = None,  # mức lương tối đa
                               keyword: str = None,  # từ khóa
                               sort_by: Optional[str] = "newest",
                               user_info: user = Depends(authorize_role(["candidate"])),
                               session: Session = Depends(get_session)):
    try:
        jobs = search_jobs(session, 
                           job_categories=job_categories,
                           min_filter=min_filter,
                           max_filter=max_filter,
                           keyword=keyword,
                           sort_by=sort_by)
        print (jobs)
        return templates.TemplateResponse("home_logged_in.html", {"request": request,
                                                                  "user_info": user_info,
                                                                  "job_descriptions": jobs})
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
    return templates.TemplateResponse("job-detail.html", {"request": request, 
                                                          "job": jd, 
                                                          "user_info": user_info})

@router.get("/job-detail/{job_id}", response_class=HTMLResponse)
def job_detail(request: Request,
               job_id: int,
               user_info: user = Depends(authorize_role(["candidate"])),
               session: Session = Depends(get_session)):
    jd = get_jd_by_id(session, job_id)
    if not jd:
        raise HTTPException(status_code=404, detail="Job not found")
    return templates.TemplateResponse("job-detail.html", {"request": request, 
                                                          "job": jd, 
                                                          "user_info": user_info})

# Lấy tất cả CVs theo username lấy từ token
@router.get("/get_cvs", response_model= List[candidate_CV])
async def get_cvs_by_username(user_info: user = Depends(authorize_role(["candidate"])),
                              session: Session = Depends(get_session)):
    return service_get_cvs_by_username(user_info.username, session)

# Trừ coin trong database
@router.post("/deduct-coin")
async def deduct_coin(amount: int, user_info: user = Depends(authorize_role(["candidate"])), session: Session = Depends(get_session)):
    '''
    True: đã trừ coin
    False: không đủ coin
    '''
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
    return templates.TemplateResponse("create-free-cv.html", {"request": request, 
                                                              "user_info": user_info})

@router.get("/mycv-settings", response_class=HTMLResponse)
async def mycv_settings(request: Request,
                  user_info: user = Depends(authorize_role(["candidate"]))):
    return templates.TemplateResponse("mycv-settings.html", {"request": request, 
                                                             "user_info": user_info})

@router.get("/finding-jobs", response_class=HTMLResponse)
async def finding_jobs(request: Request,
                       user_info: user = Depends(authorize_role(["candidate"]))):
    return templates.TemplateResponse("finding-jobs.html", {"request": request, 
                                                            "user_info": user_info})

# Tìm 10 JD phù hợp nhất với CV upload
@router.post("/top10-best-jd", response_class=HTMLResponse)
async def upload(request: Request,
                 file: UploadFile = File(...),
                 user_info: user = Depends(authorize_role(["candidate"])),
                 session: Session = Depends(get_session)):
    file_path, cv = await upload_cv(file, user_info.id, session)
    if file.content_type == "application/pdf" or file.filename.lower().endswith(".pdf"):
        from Core.OCR import scan_pdf  # hàm đọc PDF
        cv_str = scan_pdf(file_path)
    elif file.content_type.startswith("image/") or file.filename.lower().endswith((".jpg", ".jpeg", ".png")):
        from Core.OCR import run_vintern  # hàm OCR
        cv_str = run_vintern(file_path)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload a PDF or image file.")

    top_10 = get_top_10_jds_by_cv(session, cv_str)
    return templates.TemplateResponse("top10-best-jd.html", {"request": request, 
                                                             "user_info": user_info, 
                                                             "job_descriptions": top_10})

# Nộp cv cho jd bằng cv có sẵn trong database
@router.post("/submit-existing-cv", response_class=HTMLResponse)
async def submit_cv(request: Request,
                    jd_id: int,
                    existing_cv_id: int,
                    user_info: user = Depends(authorize_role(["candidate"])),
                    session: Session = Depends(get_session)):
    cv = get_candidate_cv_by_id(session, existing_cv_id) # Lấy cv trong bảng candidate_cv
    URL = cv.URL
    cv = add_cv_into_jd(session, URL, jd_id) # Add cv vào bảng jd_CV

    return templates.TemplateResponse("finding-jobs.html",{"request": request, 
                                                           "user_info": user_info})

# Nộp cv cho jd bằng cv upload từ máy
@router.post("/submit-upload-cv", response_class=HTMLResponse)
async def submit_cv(request: Request,
                    jd_id: int,
                    new_cv: Optional[UploadFile] = File(None),   # nếu upload CV mới
                    user_info: user = Depends(authorize_role(["candidate"])),
                    session: Session = Depends(get_session)):
    if not new_cv:
        raise HTTPException(status_code=400, detail="Chưa upload file")
    file_path, cv_file = await upload_cv(new_cv, user_info.id, session) # Lưu cv về server và database bảng candidate_cv
    cv = add_cv_into_jd(session, file_path, jd_id) # Add cv vào bảng jd_CV

    return templates.TemplateResponse("finding-jobs.html",{"request": request, 
                                                           "user_info": user_info})

@router.get("/pricing-user-loggedin", response_class=HTMLResponse)
async def pricing_user_logged_in(request: Request,
                                  user_info: user = Depends(authorize_role(["candidate"]))):
    
    return templates.TemplateResponse("pricing-user-loggedin.html", {"request": request, 
                                                                     "user_info": user_info})

# Lưu công việc vào danh sách yêu thích
@router.post("/save-jd", response_class=HTMLResponse)
async def save_jd(request: Request,
                  jd_id: int,
                  user_info: user = Depends(authorize_role(["candidate"])),
                  session: Session = Depends(get_session)):
    jd = service_save_jd(session, user_info.id, jd_id)
    if jd is None:
        return JSONResponse(content={"success": False, "msg": "Công việc đã được lưu trước đó."})
    
    return JSONResponse(content={"success": True, "msg": "Đã lưu công việc thành công!"})