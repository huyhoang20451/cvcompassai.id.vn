# Chứa API
from threading import Thread
from time import time
from typing import Annotated, List, Optional
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
                       get_cvs_with_top10_jds)
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

# --- Bộ nhớ lưu tiến độ công việc ---
progress_store = {}  # {"progress": int, "total": int, "done": bool}
result_store = []  # [{"jd": jd, "Ratio": float}, ...]

# --- Giả lập xử lý JD ---
def process_cv(cv_str: str):
    with Session(engine) as session:
        global progress_store, result_store
        jds = get_jds(session)
        progress_store = {"progress": 0, "total": len(jds), "done": False}
        result_store = []

        for i, jd in enumerate(jds):
            try:
                result = compare_qwen(jd_to_str(jd), cv_str)
                ratio = result.get("Ratio", 0)
                print(f"✅ JD ID: {jd.id} | Ratio: {ratio}")
                result_store.append({"jd": jd, "Ratio": ratio})
            except Exception as e:
                print(f"❌ Lỗi khi xử lý JD ID {jd.id}: {e}")
            progress_store["progress"] = i + 1
            print(f"✅ Đã xử lý JD {i}/{len(jds)}")
        
        progress_store["done"] = True

# --- Route upload CV ---
@router.post("/top10-best-jd", response_class=HTMLResponse)
async def top10_best_jd(request: Request, 
                    file: UploadFile = File(...),
                    user_info: user = Depends(authorize_role(["candidate", "candidate_premium"])),
                    session: Session = Depends(get_session)):
    file_path, cv = await service_upload_cv(file, user_info.id, session)
    if file.content_type == "application/pdf" or file.filename.lower().endswith(".pdf"):
        from Core.OCR import scan_pdf  # hàm đọc PDF
        cv_str = scan_pdf(file.file)
    elif file.content_type.startswith("image/") or file.filename.lower().endswith((".jpg", ".jpeg", ".png")):
        from Core.OCR import run_vintern  # hàm OCR
        cv_str = run_vintern(file_path)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload a PDF or image file.")
        
    # Chạy luồng nền
    thread = Thread(target=process_cv, args=(cv_str,))
    thread.start()

    # Trả về giao diện HTML hiển thị tiến trình
    html = f"""
    <html>
    <style>
        .progress-container {
            text-align: center;
            display: flex;
            margin-top: 100px;
            flex-direction: column;
            align-items: center;
        }
        .progress-container h3 {
            margin-bottom: 20px;
            font-size: 24px;
            color: #333;
        }
        .progress-container progress {
            width: 300px;
            height: 25px;
        }
    </style>
    <body>
      <div class="progress-container">
        <h3>Đang xử lý CV...</h3>
        <progress id="bar" value="0" max="10" style="width:300px;"></progress>
        <div id="status">Bắt đầu xử lý...</div>

        <script>
            const cv_id = {cv.id};  // 👈 gắn ID vào đây
            async function checkProgress() {{
                const res = await fetch(`/progress`);
                const data = await res.json();
                document.getElementById('bar').value = data.progress;
                document.getElementById('status').innerText = 
                    data.done ? "✅ Hoàn tất! Chuyển hướng tới kết quả..." :
                `Đã xử lý ${{data.progress}} / ${{data.total}} JD...`;

                if (!data.done) {{
                    setTimeout(checkProgress, 5000);
                }} else {{
                    // khi hoàn tất → chuyển tới trang kết quả
                    window.location.href = `/result?cv_id=${{data.cv_id}}`;
                }}
            }}
        checkProgress();
        </script>
    </div>
    
    </body>
    </html>
    """
    return HTMLResponse(content=html)

# --- Route cho client polling ---
@router.get("/progress")
async def get_progress():
    return JSONResponse(progress_store)

# --- Route kết quả ---
@router.get("/result", response_class=HTMLResponse)
async def result_page(request: Request,
                      cv_id: int,
                      user_info: user = Depends(authorize_role(["candidate", "candidate_premium"]))):
    result_store.sort(key=lambda x: x["Ratio"], reverse=True)
    top_10 = result_store[:10]
    top_10jd_ids = [item['jd'].id for item in top_10]
    update_candidate_cv(session=Depends(get_session),
                        cv_id=cv_id,
                        top10_jds=top_10jd_ids)
    return templates.TemplateResponse("top10-best-jd.html", {"request": request,
                                                             "cv_id": cv_id,
                                                             "job_descriptions": [jd['jd'] for jd in top_10],
                                                             "user_info": user_info})

@router.post("/create_cv")
async def create_cv(cv_data: CVData,
                    user_info=Depends(authorize_role(["candidate", "candidate_premium"])),
                    session: Session = Depends(get_session)):
    # Ví dụ: lưu vào DB, hoặc tạm thời chỉ in ra console
    print("CV nhận được:", cv_data.model_dump())

    
    return JSONResponse({"status": "ok", "name": cv_data.name, "skills_count": len(cv_data.skills)})
