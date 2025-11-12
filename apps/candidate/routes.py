# Chứa API
from threading import Thread
import threading
from time import time
from typing import Annotated, Any, Dict, List, Optional
from urllib import request
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, Cookie, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from sqlmodel import Session
from .services import (jd_to_str, search_jobs, 
                       get_cvs_by_username as service_get_cvs_by_username, 
                       get_jds, 
                       update_coin,
                       get_jd_by_id,
                       upload_cv as service_upload_cv,
                       get_candidate_cv_by_id,
                       add_cv_into_jd,
                       add_cv_into_candidate,
                       get_top_10_jds_by_cv,
                       save_jd as service_save_jd,
                       get_job_categories,
                       get_saved_jobs_by_user,
                       update_candidate_cv,
                       get_cvs_with_top10_jds,
                       get_applied_cvs)
from db import get_session, engine
from Core.Auth.schemas import user
from .schemas import CVData, JobResponse, JobSearchRequest, candidate_CV, jd
from Core.Auth.dependencies import templates, get_current_user, decode_token, authorize_role
from Core.OCR import compare_qwen, run_vintern
from ..payment.services import get_packages

router = APIRouter(tags=["candidate"])


# Home sau khi log in
@router.get("/home-logged-in", response_class=HTMLResponse)
async def home(request: Request, 
               user_info: user = Depends(authorize_role(["candidate", "candidate_premium"])), 
               session: Session = Depends(get_session)):
    job_descriptions = get_jds(session)
    job_categories = get_job_categories(session)
    return templates.TemplateResponse("home_logged_in.html", {"request": request, 
                                                              "job_descriptions": job_descriptions, 
                                                              "user_info": user_info,
                                                              "job_categories": job_categories})

@router.get("/aboutus-logged-in", response_class=HTMLResponse)
async def about_us(request: Request,
                   user_info: user = Depends(authorize_role(["candidate", "candidate_premium"]))):
    return templates.TemplateResponse("aboutus-logged-in.html", {"request": request, 
                                                                 "user_info": user_info})

@router.get("/pricing-user-logged-in", response_class=HTMLResponse)
async def pricing(request: Request,
                  user_info: user = Depends(authorize_role(["candidate", "candidate_premium"])),
                  session: Session = Depends(get_session)):
    packages = get_packages(session)
    candidate_packages = [p for p in packages if p.name.startswith("candidate_")]
    print(candidate_packages)
    return templates.TemplateResponse("pricing-user-logged-in.html", {"request": request, 
                                                                      "user_info": user_info,
                                                                      "candidate_packages": candidate_packages})

@router.get("/ocr-scan-logged-in", response_class=HTMLResponse)
async def ocr_scan(request: Request,
                   user_info: user = Depends(authorize_role(["candidate", "candidate_premium"]))):
    return templates.TemplateResponse("ocr-scan.html", {"request": request, 
                                                        "user_info": user_info})

@router.get("/finding-jobs", response_class=HTMLResponse)
async def finding_jobs(request: Request,
                       user_info: user = Depends(authorize_role(["candidate", "candidate_premium"])),
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
                               user_info: user = Depends(authorize_role(["candidate", "candidate_premium"])),
                               session: Session = Depends(get_session)):
    try:
        jobs = search_jobs(session, 
                           job_categories=job_categories,
                           min_filter=min_filter,
                           max_filter=max_filter,
                           keyword=keyword,
                           sort_by=sort_by)

        return templates.TemplateResponse("home_logged_in.html", {"request": request,
                                                                   "user_info": user_info,
                                                                   "job_descriptions": jobs})

        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")

# Màn hình chi tiết JD
@router.get("/job-detail/{job_id}", response_class=HTMLResponse)
def job_detail(request: Request,
               job_id: int,
               user_info: user = Depends(authorize_role(["candidate", "candidate_premium"])),
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
               user_info: user = Depends(authorize_role(["candidate", "candidate_premium"])),
               session: Session = Depends(get_session)):
    jd = get_jd_by_id(session, job_id)
    if not jd:
        raise HTTPException(status_code=404, detail="Job not found")
    return templates.TemplateResponse("job-detail.html", {"request": request, 
                                                          "job": jd, 
                                                          "user_info": user_info})

# Lấy tất cả CVs theo username lấy từ token
@router.get("/get_cvs", response_model= List[candidate_CV])
async def get_cvs_by_username(user_info: user = Depends(authorize_role(["candidate", "candidate_premium"])),
                              session: Session = Depends(get_session)):
    return service_get_cvs_by_username(user_info.username, session)

# Trừ coin trong database
@router.post("/deduct-coin")
async def deduct_coin(amount: int = Form(...),
                      cv_id: int = Form(...),
                      user_info: user = Depends(authorize_role(["candidate", "candidate_premium"])), 
                      session: Session = Depends(get_session)):
    '''
    True: đã trừ coin
    False: không đủ coin
    '''
    coin = user_info.coin
    if coin < amount:
        return JSONResponse(content={"success": False, "msg": "Bạn không đủ coin."})
    new_coin = coin - amount
    update_coin(session, user_info.id, new_coin)
    update_candidate_cv(session, cv_id, unlocked=True)
    return JSONResponse(content={"success": True, "coin": new_coin})

# Lấy số coin trong database
@router.get("/get-coin")
async def get_coin(user_info: user = Depends(authorize_role(["candidate", "candidate_premium"]))):
    coin = user_info.coin
    return JSONResponse(content={"success": True, "coin": coin})

@router.get("/create-free-cv", response_class=HTMLResponse)
async def create_free_cv(request: Request, 
                   user_info: user = Depends(authorize_role(["candidate", "candidate_premium"]))):
    return templates.TemplateResponse("create-free-cv.html", {"request": request, 
                                                              "user_info": user_info})

@router.get("/mycv-settings", response_class=HTMLResponse)
async def mycv_settings(request: Request,
                        user_info: user = Depends(authorize_role(["candidate", "candidate_premium"])),
                        session: Session = Depends(get_session)):
    cvs = get_cvs_with_top10_jds(user_info.username, session)
    return templates.TemplateResponse("mycv-settings.html", {"request": request, 
                                                             "user_info": user_info,
                                                             "cvs": cvs})

@router.get("/finding-jobs", response_class=HTMLResponse)
async def finding_jobs(request: Request,
                       user_info: user = Depends(authorize_role(["candidate", "candidate_premium"])),
                       session: Session = Depends(get_session)):
    jds = get_jds(session)
    return templates.TemplateResponse("finding-jobs.html", {"request": request,
                                                            "user_info": user_info,
                                                            "jds": jds})
# Nộp cv cho jd bằng cv có sẵn trong database
@router.post("/submit-existing-cv", response_class=HTMLResponse)
async def submit_cv(request: Request,
                    jd_id: int,
                    existing_cv_id: int,
                    user_info: user = Depends(authorize_role(["candidate", "candidate_premium"])),
                    session: Session = Depends(get_session)):
    cv = get_candidate_cv_by_id(session, existing_cv_id) # Lấy cv trong bảng candidate_cv
    URL = cv.URL
    cv = add_cv_into_jd(session, URL, jd_id, user_info.id) # Add cv vào bảng jd_CV

    return JSONResponse(content={"success": True, "msg": "Đã nộp CV thành công!"})

# Nộp cv cho jd bằng cv upload từ máy
@router.post("/submit-upload-cv", response_class=HTMLResponse)
async def submit_cv(request: Request,
                    jd_id: int,
                    new_cv: Optional[UploadFile] = File(None),   # nếu upload CV mới
                    user_info: user = Depends(authorize_role(["candidate", "candidate_premium"])),
                    session: Session = Depends(get_session)):
    if not new_cv:
        raise HTTPException(status_code=400, detail="Chưa upload file")
    file_path, cv_file = await service_upload_cv(new_cv, user_info.id, session) # Lưu cv về server và database bảng candidate_cv
    cv = add_cv_into_jd(session, file_path, jd_id, user_info.id) # Add cv vào bảng jd_CV

    return JSONResponse(content={"success": True, "msg": "Đã nộp CV thành công!"})

@router.get("/pricing-user-loggedin", response_class=HTMLResponse)
async def pricing_user_logged_in(request: Request,
                                  user_info: user = Depends(authorize_role(["candidate", "candidate_premium"]))):
    
    return templates.TemplateResponse("pricing-user-loggedin.html", {"request": request, 
                                                                     "user_info": user_info})

@router.get("/saved-jobs", response_class=HTMLResponse)
async def saved_jobs(request: Request,
                     user_info: user = Depends(authorize_role(["candidate", "candidate_premium"])),
                     session: Session = Depends(get_session)):
    save_jds = get_saved_jobs_by_user(session, user_info.id)
    return templates.TemplateResponse("user-cv-storage.html", {"request": request,
                                                               "user_info": user_info,
                                                               "jds": save_jds})

# Lưu công việc vào danh sách yêu thích
@router.post("/save-jd/{jd_id}", response_class=HTMLResponse)
async def save_jd(request: Request,
                  jd_id: int,
                  user_info: user = Depends(authorize_role(["candidate", "candidate_premium"])),
                  session: Session = Depends(get_session)):
    jd = service_save_jd(session, user_info.id, jd_id)
    if jd is None:
        return JSONResponse(content={"success": False, "msg": "Công việc đã được lưu trước đó."})
    
    return JSONResponse(content={"success": True, "msg": "Đã lưu công việc thành công!"})

# --- Bộ nhớ lưu tiến độ và kết quả (theo cv_id để hỗ trợ đa người dùng) ---
progress_store: Dict[int, Dict[str, Any]] = {}  # {cv_id: {"progress": int, "total": int, "done": bool, "error": str}}
result_store: Dict[int, List[Dict[str, Any]]] = {}  # {cv_id: [{"jd": jd, "Ratio": float}, ...]}
store_lock = threading.Lock()  # Bảo vệ truy cập đồng thời

# --- Giả lập xử lý JD ---
def process_cv(cv_id: int, cv_str: str, session_factory):
    session = session_factory()
    try:
        jds = get_jds(session)
        total = len(jds)

        # Khởi tạo tiến độ
        with store_lock:
            progress_store[cv_id] = {"progress": 0, "total": total, "done": False, "error": None}
            result_store[cv_id] = []

        for i, jd in enumerate(jds):
            try:
                result = compare_qwen(jd_to_str(jd), cv_str)
                ratio = result.get("Ratio", 0.0)
                print(f"✅ [CV {cv_id}] JD ID: {jd.id} | Ratio: {ratio:.2f}")

                with store_lock:
                    result_store[cv_id].append({"jd": jd, "Ratio": ratio})
                    progress_store[cv_id]["progress"] = i + 1

            except Exception as e:
                print(f"❌ [CV {cv_id}] Lỗi khi xử lý JD ID {jd.id}: {e}")
                # Ghi lỗi nhưng tiếp tục xử lý JD khác
                continue

        # Hoàn tất: sắp xếp và đánh dấu done
        with store_lock:
            if cv_id in result_store:
                result_store[cv_id].sort(key=lambda x: x["Ratio"], reverse=True)
            progress_store[cv_id]["done"] = True
            progress_store[cv_id]["progress"] = total

        print(f"✅ [CV {cv_id}] Đã xử lý xong {total} JD.")

    except Exception as e:
        with store_lock:
            progress_store[cv_id] = {
                "progress": 0,
                "total": 0,
                "done": True,
                "error": f"Lỗi hệ thống: {str(e)}"
            }
        print(f"❌ [CV {cv_id}] Lỗi nghiêm trọng trong process_cv: {e}")
    finally:
        session.close()


# --- Route upload CV ---
@router.post("/top10-best-jd", response_class=HTMLResponse)
async def top10_best_jd(
    request: Request,
    file: UploadFile = File(...),
    user_info: user = Depends(authorize_role(["candidate", "candidate_premium"])),
    session: Session = Depends(get_session)
):
    # Upload và xử lý file
    file_path, cv = await service_upload_cv(file, user_info.id, session)

    # Đọc nội dung CV
    try:
        if file.content_type == "application/pdf" or file.filename.lower().endswith(".pdf"):
            from Core.OCR import scan_pdf
            cv_str = scan_pdf(file.file)
        elif file.content_type.startswith("image/") or file.filename.lower().endswith((".jpg", ".jpeg", ".png")):
            from Core.OCR import run_vintern
            cv_str = run_vintern(file_path)
        else:
            raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file PDF hoặc ảnh (JPG, PNG).")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi đọc file: {str(e)}")

    # Xóa dữ liệu cũ nếu có (tránh trùng)
    with store_lock:
        progress_store.pop(cv.id, None)
        result_store.pop(cv.id, None)

    # Chạy nền
    thread = threading.Thread(
        target=process_cv,
        args=(cv.id, cv_str, get_session),  # get_session là callable
        daemon=True
    )
    thread.start()

    return templates.TemplateResponse(
        "progress-scancv-user.html",
        {
            "request": request,
            "user_info": user_info,
            "cv_id": cv.id
        }
    )


# --- Route polling tiến độ ---
@router.get("/progress/{cv_id}")
async def get_progress(cv_id: int):
    with store_lock:
        progress = progress_store.get(cv_id, {"progress": 0, "total": 0, "done": True, "error": "Không tìm thấy tiến độ."})
    return JSONResponse(progress)


# --- Route hiển thị kết quả ---
@router.get("/result/{cv_id}", response_class=HTMLResponse)
async def result_page(
    request: Request,
    cv_id: int,
    user_info: user = Depends(authorize_role(["candidate", "candidate_premium"])),
    session: Session = Depends(get_session)
):
    with store_lock:
        if cv_id not in result_store or cv_id not in progress_store:
            raise HTTPException(status_code=404, detail="Kết quả chưa sẵn sàng hoặc không tồn tại.")
        
        if not progress_store[cv_id]["done"]:
            raise HTTPException(status_code=425, detail="Đang xử lý, vui lòng chờ...")

        if progress_store[cv_id].get("error"):
            raise HTTPException(status_code=500, detail=progress_store[cv_id]["error"])

        results = result_store[cv_id]

    if not results:
        top_10 = []
    else:
        top_10 = results[:10]

    top_10_jd_ids = [item["jd"].id for item in top_10]

    # Cập nhật DB
    update_candidate_cv(
        session=session,
        cv_id=cv_id,
        top10_jds=top_10_jd_ids
    )

    return templates.TemplateResponse(
        "top10-best-jd.html",
        {
            "request": request,
            "cv_id": cv_id,
            "job_descriptions": [item["jd"] for item in top_10],
            "ratios": [item["Ratio"] for item in top_10],
            "user_info": user_info
        }
    )

@router.post("/create_cv")
async def create_cv(request: Request,
                    cv_data: CVData,
                    user_info=Depends(authorize_role(["candidate", "candidate_premium"])),
                    session: Session = Depends(get_session)):
    # Ví dụ: lưu vào DB, hoặc tạm thời chỉ in ra console
    print("CV nhận được:", cv_data.model_dump())

    
    return JSONResponse({"status": "ok", "name": cv_data.name, "skills_count": len(cv_data.skills)})

@router.get("/applied-cvs")
async def get_applied_cvs_endpoint(request: Request,
                                   user_info: user = Depends(authorize_role(["candidate", "candidate_premium"])),
                                   session: Session = Depends(get_session)):
    cvs = get_applied_cvs(session, user_info.id)

    return templates.TemplateResponse("applied_cvs.html", {"request": request,
                                                             "user_info": user_info,
                                                             "cvs": cvs})