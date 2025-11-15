# Chứa API
from threading import Thread
from time import time
from typing import Annotated, List, Optional
from urllib import request
import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Cookie, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from sqlmodel import Session
from .services import (get_jds_by_category, jd_to_str, search_jobs, 
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
from Core.OCR import compare_qwen, run_vintern, scan_pdf
from ..payment.services import get_packages
from threading import Lock

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
                   user_info: user = Depends(authorize_role(["candidate", "candidate_premium"])),
                   session: Session = Depends(get_session)):
    job_categories = get_job_categories(session)
    return templates.TemplateResponse("ocr-scan.html", {"request": request, 
                                                        "user_info": user_info,
                                                        "job_categories": job_categories})

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

progress_lock = Lock()
result_lock = Lock()
# --- Bộ nhớ lưu tiến độ công việc ---
progress_store = {}  # {"progress": int, "total": int, "done": bool}
result_store = []  # [{"jd": jd, "Ratio": float}, ...]

# === Hàm xử lý CV trong nền ===
def process_cv(cv_str: str, cv_id: int, user_id: int, job_category: Optional[str] = None):
    # Tạo session RIÊNG trong thread
    with Session(engine) as session:
        if job_category:
            jds = get_jds_by_category(session, job_category)
        else:
            jds = get_jds(session)

        # Reset tiến độ & kết quả
        with progress_lock:
            progress_store.clear()
            progress_store.update({
                "progress": 0,
                "total": len(jds),
                "done": False
            })
        with result_lock:
            result_store.clear()

        # Xử lý từng JD
        for i, jd in enumerate(jds):
            try:
                result = compare_qwen(jd_to_str(jd), cv_str)
                ratio = result.get("Ratio", 0.0)
                print(f"JD ID: {jd.id} | Ratio: {ratio}")

                with result_lock:
                    result_store.append({"jd": jd, "Ratio": ratio})

            except Exception as e:
                print(f"Lỗi khi xử lý JD ID {jd.id}: {e}")

            # Cập nhật tiến độ
            with progress_lock:
                progress_store["progress"] = i + 1
            print(f"Đã xử lý JD {i+1}/{len(jds)}")

        # Hoàn tất
        with progress_lock:
            progress_store["done"] = True

        # Cập nhật top 10 JD vào DB
        top_10 = sorted(result_store, key=lambda x: x["Ratio"], reverse=True)[:10]
        top10_jd_ids = [item["jd"].id for item in top_10]
        update_candidate_cv(session, cv_id=cv_id, top10_jds=top10_jd_ids)
        session.commit()


# === Route: Upload CV + Bắt đầu xử lý ===
@router.post("/top10-best-jd", response_class=HTMLResponse)
async def top10_best_jd(
    request: Request,
    background_tasks: BackgroundTasks,  # <-- ĐƯA LÊN TRƯỚC
    file: UploadFile = File(...),
    job_category: Optional[str] = Form(None),
    user_info: user = Depends(authorize_role(["candidate", "candidate_premium"])),
    session: Session = Depends(get_session)
):
    # Upload CV
    file_path, cv = await service_upload_cv(file, user_info.id, session)

    # OCR: Đọc nội dung CV
    if file.content_type == "application/pdf" or file.filename.lower().endswith(".pdf"):
        cv_str = scan_pdf(file.file)
    elif file.content_type.startswith("image/") or file.filename.lower().endswith((".jpg", ".jpeg", ".png")):
        cv_str = run_vintern(file_path)
    else:
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ PDF hoặc ảnh (JPG, PNG).")

    # Chạy xử lý nền (an toàn với FastAPI)
    background_tasks.add_task(process_cv, cv_str, cv.id, user_info.id, job_category)

    # Trả về trang loading
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Đang xử lý CV...</title>
        <style>
            .progress-container {{
                text-align: center;
                margin-top: 100px;
                font-family: Arial, sans-serif;
            }}
            h3 {{
                color: #333;
                margin-bottom: 20px;
            }}
            progress {{
                width: 400px;
                height: 30px;
            }}
            #status {{
                margin-top: 15px;
                font-size: 18px;
            }}
        </style>
    </head>
    <body>
        <div class="progress-container">
            <h3>Đang phân tích CV của bạn...</h3>
            <progress id="bar" value="0" max="100"></progress>
            <div id="status">Bắt đầu xử lý...</div>
        </div>

        <script>
            const cv_id = {cv.id};
            async function checkProgress() {{
                try {{
                    const res = await fetch('/progress');
                    const data = await res.json();
                    const percent = data.total > 0 ? (data.progress / data.total) * 100 : 0;
                    document.getElementById('bar').value = percent;
                    document.getElementById('status').innerText = 
                        data.done 
                            ? "Hoàn tất! Đang chuyển hướng..." 
                            : `Đã xử lý ${{data.progress}} / ${{data.total}} công việc...`;

                    if (!data.done) {{
                        setTimeout(checkProgress, 3000);
                    }} else {{
                        setTimeout(() => {{
                            window.location.href = `/result?cv_id=${{cv_id}}`;
                        }}, 1000);
                    }}
                }} catch (e) {{
                    console.error("Lỗi kiểm tra tiến độ:", e);
                    setTimeout(checkProgress, 5000);
                }}
            }}
            checkProgress();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# === Route: Lấy tiến độ ===
@router.get("/progress")
async def get_progress():
    with progress_lock:
        return JSONResponse(progress_store.copy())


# === Route: Hiển thị kết quả top 10 JD ===
@router.get("/result", response_class=HTMLResponse)
async def result_page(
    request: Request,
    cv_id: int,
    user_info: user = Depends(authorize_role(["candidate", "candidate_premium"])),
    session: Session = Depends(get_session)
):
    # Kiểm tra xem xử lý đã xong chưa
    with progress_lock:
        if not progress_store.get("done", False):
            raise HTTPException(status_code=400, detail="CV đang được xử lý, vui lòng đợi...")

    # Lấy kết quả từ bộ nhớ
    with result_lock:
        if not result_store:
            raise HTTPException(status_code=404, detail="Không tìm thấy kết quả.")

        result_store.sort(key=lambda x: x["Ratio"], reverse=True)
        top_10 = result_store[:10]
        job_descriptions = [item["jd"] for item in top_10]

    return templates.TemplateResponse(
        "top10-best-jd.html",
        {
            "request": request,
            "cv_id": cv_id,
            "job_descriptions": job_descriptions,
            "user_info": user_info
        }
    )

@router.post("/create_cv")
async def create_cv(cv_data: CVData,
                    user_info=Depends(authorize_role(["candidate", "candidate_premium"])),
                    session: Session = Depends(get_session)):
    # Ví dụ: lưu vào DB, hoặc tạm thời chỉ in ra console
    print("CV nhận được:", cv_data.model_dump())

    
    return JSONResponse({"status": "ok", "name": cv_data.name, "skills_count": len(cv_data.skills)})
