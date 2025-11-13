# Chứa API
from threading import Thread
from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlmodel import Session
from .services import (get_jds_by_user_name, 
                       add_jd, 
                       OCR, 
                       get_cvs_by_jd_id, 
                       detect_file_type,
                       get_jd_by_id,
                       delete_jd_by_id as service_delete_jd_by_id,
                       update_jd_by_id as service_update_jd_by_id,
                       update_business_by_id as service_update_business_info,
                       get_job_categories,
                       get_total_cv_by_business_id,
                       get_total_jd_by_business_id,
                       approve_cv as service_approve_cv,
                       count_approved_cv_by_company,
                       count_saved_jobs_by_company)
from db import get_session, engine
from Core.Auth.dependencies import templates, authorize_role
from Core.Auth.schemas import user
from Core.Auth.services import get_user_by_id
from .schemas import EmailRequest, JD_create
from datetime import datetime, timezone
from typing import Optional
from Core.OCR import compare
from ..payment.services import get_packages

router = APIRouter(tags=["business"])

@router.get("/business-home", response_class=HTMLResponse)
async def business_home(request: Request):
    return templates.TemplateResponse("home-business.html", {"request": request})

@router.get("/business-dashboard", response_class=HTMLResponse)
async def business_dashboard(request: Request,
                             user_info: user = Depends(authorize_role(["business", "business_premium"])),
                             session: Session = Depends(get_session)):
    job_descriptions = get_jds_by_user_name(session, user_info.username)
    total_cv = get_total_cv_by_business_id(session, user_info.id)
    total_jd = get_total_jd_by_business_id(session, user_info.id)
    return templates.TemplateResponse("business_dashboard.html", {"request": request,
                                                                  "job_descriptions": job_descriptions,
                                                                  "user_info": user_info,
                                                                  "total_cv": total_cv,
                                                                  "total_jd": total_jd})

# Direct tới business profile page
@router.get("/business-profile", response_class=HTMLResponse)
async def business_profile(request: Request,
                           user_info: user = Depends(authorize_role(["business", "business_premium"]))):
    return templates.TemplateResponse("business_profile.html", {"request": request,
                                                                "user_info": user_info})

@router.get("/pricing-business-logged-in", response_class=HTMLResponse)
async def pricing_business_logged_in(request: Request, 
                                     user_info: user = Depends(authorize_role(["business", "business_premium"])),
                                     session: Session = Depends(get_session)):
    packages = get_packages(session)
    business_packages = [p for p in packages if p.name.startswith("business_")]
    return templates.TemplateResponse("pricing_business_logged_in.html", {"request": request, 
                                                                          "user_info": user_info,
                                                                          "business_packages": business_packages})

@router.get("/job-storage", response_class=HTMLResponse)
async def job_storage(request: Request,
                      jd_id: Optional[int] = None,
                      user_info: user = Depends(authorize_role(["business", "business_premium"])),
                      session : Session = Depends(get_session)):
    job_descriptions = get_jds_by_user_name(session, user_info.username)
    job = next((jd for jd in job_descriptions if jd.id == jd_id), None)
    return templates.TemplateResponse("job-storage.html", 
                                      {"request": request,
                                       "job_position": job_descriptions,
                                       "job": job,
                                       "user_info": user_info})

@router.post("/submit-job", response_class=HTMLResponse)
async def submit_job(request: Request, 
                     user_info: user = Depends(authorize_role(["business", "business_premium"])),
                     session: Session = Depends(get_session)):
    form = await request.form()
    jd_form = dict(form)
    
    # Chuyển các giá trị form từ list có 1 phần tử sang giá trị đơn
    for k, v in list(jd_form.items()):
        if isinstance(v, (list, tuple)) and len(v) == 1:
            jd_form[k] = v[0]

    if "job_title" in jd_form:
        jd_form["title"] = jd_form["job_title"]
        del jd_form["job_title"]
    
    jd_form["business_id"] = user_info.id
    jd_form["created_at"] = datetime.now(timezone.utc)
    jd_form = JD_create(**jd_form)
    jd = add_jd(session, jd_form)

    return RedirectResponse(url=f"/job-storage?company={user_info.company_name}&username={user_info.username}", status_code=303)

@router.get("/dang-tuyen-ngay", response_class=HTMLResponse)
def dang_tuyen_ngay(request: Request, 
                    user_info: user = Depends(authorize_role(["business", "business_premium"])),
                    session: Session = Depends(get_session)):
    job_categories = get_job_categories(session)

    return templates.TemplateResponse("form-dang-tuyen-ngay.html", {"request": request, 
                                                                    "user_info": user_info,
                                                                    "job_categories": job_categories})

@router.get("/cv-detail-business", response_class=HTMLResponse)
def cv_detail_business(request: Request, 
                       user_info: user = Depends(authorize_role(["business", "business_premium"]))):
    return templates.TemplateResponse("cv-detail-business.html", {"request": request, 
                                                                  "user_info": user_info})

#@router.get("/compare_cv_vs_jd", response_class=HTMLResponse)
#def compare_cv_vs_jd(request: Request,
#                     jd_id: int, 
#                     user_info: user = Depends(authorize_role(["business", "business_premium"])),
#                     session: Session = Depends(get_session)):
#    cvs = get_cvs_by_jd_id(session, jd_id)
#    jd = get_jd_by_id(session, jd_id)
#    results = []
#    for cv in cvs:
#        file_type = detect_file_type(cv.URL)
#        comparison = compare(cv.URL, jd, file_type)
#        results.append({"cv_url": cv.URL,
#                        "met": comparison.get("Met", []),
#                        "not_met": comparison.get("Not_Met", []),
#                        "id": cv.id})
#    print(results)
#    return templates.TemplateResponse("cv-detail-business.html", {"request": request,
#                                                                  "user_info": user_info,
#                                                                  "results": results})

compare_progress_store = {}
compare_result_store = []

def process_compare_cv_vs_jd(jd_id: int):

    with Session(engine) as session:
        global compare_progress_store, compare_result_store
        jd = get_jd_by_id(session, jd_id)
        cvs = get_cvs_by_jd_id(session, jd_id)

        total = len(cvs)
        compare_progress_store = {"progress": 0, "total": total, "done": False}
        compare_result_store = []

        for i, cv in enumerate(cvs):
            try:
                file_type = detect_file_type(cv.URL)
                comparison = compare(cv.URL, jd, file_type)
                compare_result_store.append({
                    "cv_url": cv.URL,
                    "met": comparison.get("Met", []),
                    "not_met": comparison.get("Not_Met", []),
                    "id": cv.id
                })
                print(f"✅ CV ID {cv.id} done ({i+1}/{total})")
            except Exception as e:
                print(f"❌ Error with CV {cv.id}: {e}")

            compare_progress_store["progress"] = i + 1
        
        compare_progress_store["done"] = True

@router.get("/compare_cv_vs_jd", response_class=HTMLResponse)
def compare_cv_vs_jd_start(request: Request,
                           jd_id: int,
                           user_info: user = Depends(authorize_role(["business", "business_premium"]))):
    # Chạy luồng nền
    thread = Thread(target=process_compare_cv_vs_jd, args=(jd_id,))
    thread.start()

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
        <h3>Đang so sánh CVs với JD ID {jd_id}...</h3>
        <progress id="bar" value="0" max="10" style="width:300px;"></progress>
        <div id="status">Bắt đầu xử lý...</div>
      </div>

      <script>
        const jd_id = {jd_id};
        async function checkProgress() {{
            const res = await fetch(`/compare_progress`);
            const data = await res.json();
            document.getElementById('bar').value = data.progress;
            document.getElementById('status').innerText = 
                data.done ? "✅ Hoàn tất! Chuyển hướng tới kết quả..." :
                `Đã xử lý ${{data.progress}} / ${{data.total}} CV...`;

            if (!data.done) {{
                setTimeout(checkProgress, 5000);
            }} else {{
                window.location.href = `/compare_cv_vs_jd/result?jd_id=${{jd_id}}`;
            }}
        }}
        checkProgress();
      </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@router.get("/compare_progress")
async def get_compare_progress():
    return JSONResponse(compare_progress_store)

@router.get("/compare_cv_vs_jd/result", response_class=HTMLResponse)
def compare_cv_vs_jd_result(request: Request,
                            jd_id: int,
                            user_info: user = Depends(authorize_role(["business", "business_premium"]))):
    return templates.TemplateResponse(
        "cv-detail-business.html",
        {
            "request": request,
            "user_info": user_info,
            "results": compare_result_store,
            "jd_id": jd_id
        }
    )

# Update jd by job.id
@router.post("/update-jd/{jd_id}", response_class=HTMLResponse)
async def update_jd(request: Request,
                    jd_id: Optional[int] = None,
                    user_info: user = Depends(authorize_role(["business", "business_premium"])),
                    session: Session = Depends(get_session)):
    form = await request.form()
    jd_form = dict(form)
    
    # Normalize form values: if form provides single-item lists, convert to plain values
    for k, v in list(jd_form.items()):
        if isinstance(v, (list, tuple)) and len(v) == 1:
            jd_form[k] = v[0]

    # Map các field name từ form HTML sang schema
    if "job_title" in jd_form:
        jd_form["title"] = jd_form["job_title"]
        del jd_form["job_title"]

    # Map template's `description` -> model `job_description`
    if "description" in jd_form:
        jd_form["job_description"] = jd_form.pop("description")

    # prefer path param jd_id if provided, otherwise use form id
    if jd_id is None:
        jd_id = int(jd_form.get("id"))
    else:
        # ensure form id is set for consistency
        jd_form["id"] = jd_id
    result = service_update_jd_by_id(session, jd_id, jd_form)
    if result is False:
        raise HTTPException(status_code=404, detail="Job description not found")
    return RedirectResponse(url=f"/job-storage?company={user_info.company_name}&username={user_info.username}&jd_id={jd_id}", status_code=303)

@router.post("/delete-jd/{jd_id}", response_class=HTMLResponse)
def delete_jd_by_id(request: Request,
                    jd_id: int,
                    session: Session = Depends(get_session),
                    user_info: user = Depends(authorize_role(["business", "business_premium"]))):
    result = service_delete_jd_by_id(session, jd_id, user_info.id)
    if result is False:
        raise HTTPException(status_code=404, detail="Job description not found or not authorized to delete")
    return RedirectResponse(url=f"/job-storage?company={user_info.company_name}&username={user_info.username}", status_code=303)

# Update business profile
@router.post("/update-business-profile", response_class=HTMLResponse)
async def update_business_info(request: Request,
                               session: Session = Depends(get_session),
                               user_info: user = Depends(authorize_role(["business", "business_premium"]))):
    form = await request.form()
    business_info = dict(form)
    print(business_info)
    result = service_update_business_info(session, user_info.id, business_info)
    if result is False:
        raise HTTPException(status_code=404, detail="Business information not found")
    return RedirectResponse(url=f"/business-profile", status_code=303)

@router.post("/approve-cv", response_class=HTMLResponse)
async def approve_cv(request: Request,
                     id: int = Form(...),
                     approval: bool = Form(...),
                     session: Session = Depends(get_session),
                     user_info: user = Depends(authorize_role(["business", "business_premium"]))):

    result = service_approve_cv(session, id, approval)
    if result is False:
        raise HTTPException(status_code=404, detail="CV not found or not authorized to approve")
    if approval:
        return JSONResponse(content={"message": "CV approved successfully"})
    else:
        return JSONResponse(content={"message": "CV rejected successfully"})

@router.get("/count-approved-cvs", response_class=HTMLResponse)
async def count_approved_cvs(request: Request,
                             session: Session = Depends(get_session),
                             user_info: user = Depends(authorize_role(["business", "business_premium"]))):

    result = count_approved_cv_by_company(session, user_info.id)
    if result is False:
        raise HTTPException(status_code=404, detail="CV not found or not authorized to approve")
    return JSONResponse(content={"count": result})

@router.get("/count-saved-jobs", response_class=HTMLResponse)
async def count_saved_jobs(request: Request,
                           session: Session = Depends(get_session),
                           user_info: user = Depends(authorize_role(["business", "business_premium"]))):

    result = count_saved_jobs_by_company(session, user_info.id)
    if result is False:
        raise HTTPException(status_code=404, detail="CV not found or not authorized to approve")
    return JSONResponse(content={"count": result})
