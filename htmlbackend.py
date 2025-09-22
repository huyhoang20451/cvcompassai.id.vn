import json
import os
import math
from fastapi import FastAPI, HTTPException, Form, Request, requests
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import List, Optional
# File is not defined


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Đường dẫn folder templates
templates = Jinja2Templates(directory="templates")

# File JSON lưu user
USER_FILE = "database/users.json"
JD_FILE = "database/job-description.json"

# Load the model
class job_description(BaseModel):
    id: int
    company_logo: str
    job_title: str
    company_name: str
    salary: str
    location: str
    industry: str
    position: str
    company: str
    workplace: str
    job_description: List[str]
    requirements: List[str]
    benefits: List[str]
    working_time: str
    application_method: str
    deadline: str

# Hàm load các jd vào trang Cơ hội tuyển dụng
def load_jd() -> List[job_description]:
    with open(JD_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_job_detail_by_id(job_id: int) -> job_description | None:
    all_jobs = load_jd()
    job = next((item for item in all_jobs if item["id"] == job_id), None)
    return job

# Viết hàm load ra các vị trí có id = với tên đang đăng nhập
def load_jd_by_company(company: str) -> List[job_description]:
    all_jobs = load_jd()
    company_jobs = [job for job in all_jobs if job["company"] == company]
    return company_jobs

# Hàm tìm kiếm job theo từ khóa
def search_jobs_by_keyword(keyword: str) -> List[job_description]:
    all_jobs = load_jd()
    if not keyword:
        return all_jobs
    
    keyword_lower = keyword.lower()
    filtered_jobs = []
    
    for job in all_jobs:
        # Tìm kiếm trong job_title, company_name, industry, location
        if (keyword_lower in job.get("job_title", "").lower() or
            keyword_lower in job.get("company_name", "").lower() or
            keyword_lower in job.get("industry", "").lower() or
            keyword_lower in job.get("location", "").lower() or
            keyword_lower in job.get("position", "").lower()):
            filtered_jobs.append(job)
    
    return filtered_jobs 

# Băm mật khẩu
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ==== Hàm tiện ích ====
def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_users(users):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

# ==== ROUTES ====

#---------------------------------

# Route đăng ký: nhận dữ liệu từ form

@app.post("/signup", response_class=HTMLResponse)
def signup(request: Request, username: str = Form(...), password: str = Form(...), role: str = Form("user"), company: str = Form(None)):
    users = load_users()
    if username in users:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Tên người dùng đã tồn tại"})

    hashed_pw = pwd_context.hash(password)
    user_data = {"username": username, "password": hashed_pw, "role": role, "coin": 10}
    if role == "business" and company:
        user_data["company"] = company
    users[username] = user_data
    save_users(users)

    # Chuyển về trang login và truyền thông báo thành công
    return templates.TemplateResponse("login.html", {"request": request, "success": "Đăng ký thành công"})
    
# Đăng nhập
@app.post("/login", response_class=HTMLResponse)
def login(username: str = Form(...), password: str = Form(...)):
    users = load_users()
    user = users.get(username)

    if not user or not pwd_context.verify(password, user["password"]):
        raise HTTPException(status_code=400, detail="Sai tên đăng nhập hoặc mật khẩu")

    user_role = user.get("role", "business")
    company = user.get("company", "")

    # Trả về trang HTML chào mừng
    if user_role == "business":
        return RedirectResponse(url=f"/business-dashboard?username={username}&role={user_role}&company={company}", status_code=303)
    else:
        return RedirectResponse(url=f"/home-logged-in?username={username}&role={user_role}", status_code=303)
#---------------------------------

# Trang đăng ký
@app.get("/signup", response_class=HTMLResponse)
def signup_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# Xử lý đăng ký
@app.post("/signup")
def signup(username: str = Form(...), password: str = Form(...), role: str = Form("user"), company: str = Form(None)):
    users = load_users()
    if username in users:
        raise HTTPException(status_code=400, detail="Tên người dùng đã tồn tại")

    hashed_pw = pwd_context.hash(password)
    user_data = {"username": username, "password": hashed_pw, "role": role}
    if role == "business" and company:
        user_data["company"] = company
    users[username] = user_data
    save_users(users)

    return RedirectResponse(url="/login", status_code=303)

# Trang đăng nhập
@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Xử lý đăng nhập
@app.post("/login", response_class=HTMLResponse)
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    users = load_users()
    user = users.get(username)

    if not user or not pwd_context.verify(password, user["password"]):
        raise HTTPException(status_code=400, detail="Sai tên đăng nhập hoặc mật khẩu")

    # Lấy quyền người dùng
    user_role = user.get("role", "business")
    company = user.get("company", "")

    # Chuyển hướng kèm role (nếu cần dùng ở template, có thể truyền qua session hoặc query)
    if user_role == "business":
        return RedirectResponse(url=f"/business-dashboard?username={username}&role={user_role}&company={company}", status_code=303)
    else:
        return RedirectResponse(url=f"/home-logged-in?username={username}&role={user_role}", status_code=303)

#-------------------------chuyen trang khi da dang nhap---------------------------------------------
# Trang home (sau khi login)
@app.get("/home-logged-in", response_class=HTMLResponse)
def home_logged_in(request: Request, username: str, keyword: str = ""):
    # Nếu có keyword thì lọc kết quả, ngược lại show tất cả
    if keyword:
        job_descriptions = search_jobs_by_keyword(keyword)
    else:
        job_descriptions = load_jd()
    templates = Jinja2Templates(directory="templates")
    return templates.TemplateResponse("home_logged_in.html", {"request": request, "job_descriptions": job_descriptions, "username": username, "keyword": keyword})

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    # Load job descriptions
    job_descriptions = load_jd()
    templates = Jinja2Templates(directory="templates")
    return templates.TemplateResponse("home.html", {"request": request, "job_descriptions": job_descriptions})

@app.get("/aboutus-logged-in", response_class=HTMLResponse)
def about_us(request: Request, username: str):
    return templates.TemplateResponse("aboutus-logged-in.html", {"request": request, "username": username})

@app.get("/pricing-user-loggedin", response_class=HTMLResponse)
def pricing(request: Request, username: str):
    return templates.TemplateResponse("pricing-user-loggedin.html", {"request": request, "username": username})

@app.get("/ocr-scan-logged-in", response_class=HTMLResponse)
def ocr_scan(request: Request, username: str):
    return templates.TemplateResponse("ocr-scan.html", {"request": request, "username": username})

@app.get('/top10-best-jd', response_class=HTMLResponse)
def top10_best_jd(request: Request, username: str):
    job_descriptions = load_jd()
    return templates.TemplateResponse("top10-best-jd.html", {
        "request": request,
        "username": username,
        "job_descriptions": job_descriptions
    })
    raise HTTPException(status_code=404, detail="Job not found")
    return templates.TemplateResponse("top10-best-jd.html", {"request": request, "username": username, "coin": coin, "job_description": job_description})

@app.get('/top10-best-jd-detail', response_class=HTMLResponse)
def top10_best_jd_detail(request: Request, username: str):
    job_description = load_jd()
    users = load_users()
    user = users.get(username)
    coin = user.get("coin", 0) if user else 0
    if not job_description:
        raise HTTPException(status_code=404, detail="Job not found")
    return templates.TemplateResponse("top10-best-jd-detail.html", {"request": request, "username": username, "coin": coin, "job_description": job_description})

#-----------------------------------------------------------------------------------------
#---------------------------- chuyen trang chua dang nhap---------------------------------------------
@app.get("/aboutus", response_class=HTMLResponse)
def about_us(request: Request):
    return templates.TemplateResponse("about-us.html", {"request": request})

@app.get("/home", response_class=HTMLResponse)
def home(request: Request):
    job_descriptions = load_jd()
    templates = Jinja2Templates(directory="templates")
    return templates.TemplateResponse("home.html", {"request": request, "job_descriptions": job_descriptions})

@app.get("/pricing", response_class=HTMLResponse)
def pricing(request: Request):
    return templates.TemplateResponse("pricing.html", {"request": request})

# Route tìm kiếm job theo từ khóa
@app.get("/search-jobs", response_class=HTMLResponse)
def search_jobs(request: Request, keyword: str = "", username: str = ""):
    if keyword:
        job_descriptions = search_jobs_by_keyword(keyword)
    else:
        job_descriptions = load_jd()
    
    return templates.TemplateResponse("search-results.html", {
        "request": request, 
        "job_descriptions": job_descriptions, 
        "keyword": keyword,
        "username": username
    })

# Route xử lý form tìm kiếm (POST)
@app.post("/search-jobs", response_class=HTMLResponse)
def search_jobs_post(request: Request, keyword: str = Form(""), username: str = Form("")):
    return RedirectResponse(url=f"/search-jobs?keyword={keyword}&username={username}", status_code=303)

# Viết trang khi click vào 1 job cần quan tâm, chuyển sang trang chi tiết
@app.get("/job-detail/{job_id}", response_class=HTMLResponse)
def job_detail(request: Request, username: str, job_id: int):
    job_descriptions = load_jd()
    
    # job_descriptions bây giờ là list dict, tìm job theo id
    job = next((item for item in job_descriptions if item["id"] == job_id), None)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Truyền job dict sang template
    return templates.TemplateResponse(
        "job-detail.html", 
        {"request": request, "job": job, "username": username}
    )

@app.get("/business-home", response_class=HTMLResponse)
def business_home(request: Request):
    return templates.TemplateResponse("home-business.html", {"request": request})

@app.get("/business-dashboard", response_class=HTMLResponse)
def business_dashboard(request: Request, username: str = None, company: str = None):
    # Nếu company chưa truyền qua query, lấy từ users.json
    if not company and username:
        users = load_users()
        user = users.get(username)
        company = user.get("company", "") if user else ""
    return templates.TemplateResponse("business_dashboard.html", {"request": request, "username": username, "company": company})

@app.get("/pricing-business-logged-in", response_class=HTMLResponse)
def pricing_business_logged_in(request: Request, username: str, company: str):
    return templates.TemplateResponse("pricing_business_logged_in.html", {"request": request, "username": username, "company": company})

@app.get("/top10-best-jd-unblur", response_class=HTMLResponse)
def top10_best_jd_unblur(request: Request, username: str):
    job_descriptions = load_jd()[:10]  # Lấy đúng 10 JD
    return templates.TemplateResponse("top10-best-jd-unblur.html", {"request": request, "job_descriptions": job_descriptions, "username": username})

@app.get("/api/deduct-coin")
def deduct_coin(username: str, amount: int):
    users = load_users()
    user = users.get(username)
    if not user:
        return JSONResponse(content={"success": False, "msg": "Không tìm thấy người dùng."})
    coin = user.get("coin", 0)
    if coin < amount:
        return JSONResponse(content={"success": False, "msg": "Bạn không đủ coin."})
    user["coin"] = coin - amount
    save_users(users)
    return JSONResponse(content={"success": True, "coin": user["coin"]})

@app.get("/api/get-coin")
def get_coin(username: str):
    users = load_users()
    user = users.get(username)
    if not user:
        return {"success": False, "msg": "Không tìm thấy người dùng.", "coin": 0}
    coin = user.get("coin", 0)
    return {"success": True, "coin": coin}

# When click on the job on top-10-best-jd-unblur, go to detail page with unblurred content
@app.get("/top10-best-jd-detail-unblur/job_id={job_id}", response_class=HTMLResponse)
def top10_best_jd_detail_unblur(request: Request, username: str, job_id: int):
    job_descriptions = load_jd()
    job = next((item for item in job_descriptions if item["id"] == job_id), None)
    users = load_users()
    user = users.get(username)
    coin = user.get("coin", 0) if user else 0
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return templates.TemplateResponse("top10-best-jd-detail-unblur.html", {"request": request, "job": job, "job_descriptions": job_descriptions, "username": username, "coin": coin})

@app.get("/create-free-cv", response_class=HTMLResponse)
def create_free_cv(request: Request):
    return templates.TemplateResponse("create-free-cv.html", {"request": request})

@app.get("/job-storage", response_class=HTMLResponse)
def job_storage(request: Request, company: str, username: str):
    job_descriptions = load_jd()
    users = load_users()
    user = users.get(username)
    company = user.get("company", "") if user else ""
    job_position = load_jd_by_company(company)
    return templates.TemplateResponse("job-storage.html", {"request": request, "company": company, "username": username, "job_position": job_position, "job_descriptions": job_descriptions})

@app.get("/job-storage/{job_id}", response_class=HTMLResponse)
def job_storage_detail(request: Request, company: str, username: str, job_id: int):
    job_descriptions = load_jd()
    users = load_users()
    user = users.get(username)
    company = user.get("company", "") if user else ""
    job_position = load_jd_by_company(company)
    job = get_job_detail_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return templates.TemplateResponse("job-storage.html", {"request": request, "company": company, "username": username, "job_position": job_position, "job_descriptions": job_descriptions, "job": job})

@app.post("/submit-job", response_class=HTMLResponse)
def submit_job(request: Request, company_logo: str = Form(...), job_title: str = Form(...), company_name: str = Form(...), salary: str = Form(...), location: str = Form(...), industry: str = Form(...), position: str = Form(...), company: str = Form(...), workplace: str = Form(...), job_description: str = Form(...), requirements: str = Form(...), benefits: str = Form(...), working_time: str = Form(...), application_method: str = Form(...), deadline: str = Form(...), username: str = Form(...)):
    job_descriptions = load_jd()
    new_id = max([job["id"] for job in job_descriptions], default=0) + 1
    # Tìm company_id cho công ty này, nếu chưa có thì gán mới
    company_ids = {job["company"]: job["company_id"] for job in job_descriptions if "company_id" in job}
    if company in company_ids:
        company_id = company_ids[company]
    else:
        company_id = max(company_ids.values(), default=0) + 1
    new_job = {
        "id": new_id,
        "company_id": company_id,
        "company_logo": company_logo,
        "job_title": job_title,
        "company_name": company_name,
        "salary": salary,
        "location": location,
        "industry": industry,
        "position": position,
        "company": company,
        "workplace": workplace,
        "job_description": job_description.split("\n"),
        "requirements": requirements.split("\n"),
        "benefits": benefits.split("\n"),
        "working_time": working_time,
        "application_method": application_method,
        "deadline": deadline
    }
    job_descriptions.append(new_job)
    with open(JD_FILE, "w", encoding="utf-8") as f:
        json.dump(job_descriptions, f, ensure_ascii=False, indent=4)
    return RedirectResponse(url=f"/job-storage?company={company}&username={username}", status_code=303)


@app.get("/dang-tuyen-ngay", response_class=HTMLResponse)
def dang_tuyen_ngay(request: Request, username: str):
    users = load_users()
    user = users.get(username)
    company = user.get("company", "") if user else ""
    return templates.TemplateResponse("form-dang-tuyen-ngay.html", {"request": request, "username": username, "company": company})

@app.get("/cv-detail-business", response_class=HTMLResponse)
def cv_detail_business(request: Request, username: str):
    users = load_users()
    user = users.get(username)
    company = user.get("company", "") if user else ""
    return templates.TemplateResponse("cv-detail-business.html", {"request": request, "username": username, "company": company})

# @app.get("/ho-so-cua-toi", response_class=HTMLResponse)
# def ho_so_cua_toi(request: Request, username: str):
#     users = load_users()
#     user = users.get(username)
#     return templates.TemplateResponse("ho-so-cua-toi.html", {"request": request, "username": username, "user": user})

@app.get("/edit-profile", response_class=HTMLResponse)
def edit_profile(request: Request, username: str):
    users = load_users()
    user = users.get(username)
    return templates.TemplateResponse("settings.html", {"request": request, "username": username, "user": user})

@app.get("/mycv-settings", response_class=HTMLResponse)
def mycv_settings(request: Request, username: str):
    users = load_users()
    user = users.get(username)
    return templates.TemplateResponse("mycv-settings.html", {"request": request, "username": username, "user": user})

@app.get("/system-settings", response_class=HTMLResponse)
def system_settings(request: Request, username: str):
    users = load_users()
    user = users.get(username)
    return templates.TemplateResponse("system-settings.html", {"request": request, "username": username, "user": user})

@app.get("/finding-jobs", response_class=HTMLResponse)
def finding_jobs(request: Request, username: str):
    users = load_users()
    user = users.get(username)
    return templates.TemplateResponse("finding-jobs.html", {"request": request, "username": username, "user": user})

@app.api_route("/payment", methods=["GET", "POST"], response_class=HTMLResponse)
async def payment(request: Request, username: str = None):
    """Handle payment page for GET and POST.
    Accepts query params or form data. For the 'xu' package we parse
    `price` and `quantity` safely (empty strings fallback to defaults)
    and compute total values to pass to the template.
    """
    package = None

    # Extract package and username from form (POST) or query params (GET)
    if request.method == "POST":
        form = await request.form()
        package = form.get("package") or None
        if not username:
            username = form.get("username") or None
    else:
        qp = request.query_params
        package = qp.get("package") or None
        if not username:
            username = qp.get("username") or None

    users = load_users()
    user = users.get(username) if username else None

    if package == 'premium':
        return templates.TemplateResponse(
            "payment-premium.html",
            {"request": request, "username": username, "user": user, "package": package},
        )

    if package == 'xu':
        # Defaults
        default_price = 10000
        default_quantity = 1
        xu_per_pack = 2

        # Read raw inputs
        if request.method == 'POST':
            form = await request.form()
            raw_price = form.get('price')
            raw_quantity = form.get('quantity')
            # support client sending requested xu amount
            raw_xu_requested = form.get('xu') or form.get('xu_requested')
        else:
            qp = request.query_params
            raw_price = qp.get('price')
            raw_quantity = qp.get('quantity')
            raw_xu_requested = qp.get('xu') or qp.get('xu_requested')

        # Safe parsing helper: treat None or empty string as fallback
        def safe_int(val, fallback):
            if val is None:
                return fallback
            if isinstance(val, int):
                return val
            s = str(val).strip()
            if s == "":
                return fallback
            try:
                return int(s)
            except (ValueError, TypeError):
                return fallback

        price_val = safe_int(raw_price, default_price)
        quantity_val = safe_int(raw_quantity, default_quantity)

        # If client provided desired xu count, compute required packs (ceil)
        xu_requested = safe_int(raw_xu_requested, None) if 'raw_xu_requested' in locals() else None
        if xu_requested is not None:
            # compute number of packs needed to reach at least xu_requested
            packs_needed = math.ceil(xu_requested / xu_per_pack) if xu_per_pack > 0 else quantity_val
            quantity_val = max(quantity_val, packs_needed)

        if quantity_val < 1:
            quantity_val = 1

        total_price = price_val * quantity_val
        total_xu = xu_per_pack * quantity_val

        return templates.TemplateResponse(
            "payment-coin.html",
            {
                "request": request,
                "username": username,
                "user": user,
                "package": package,
                "price": price_val,
                "quantity": quantity_val,
                "total": total_price,
                "xu_per_pack": xu_per_pack,
                "total_xu": total_xu,
            },
        )

    # If package not recognized, show a generic page or 400
    raise HTTPException(status_code=400, detail="Missing or invalid package")

@app.get("/premium-checkout", response_class=HTMLResponse)
def premium_checkout(request: Request, username: Optional[str] = None, package: Optional[str] = None, price: Optional[int] = 0, quantity: Optional[int] = 1):
    """Render the premium checkout page. All query parameters are optional so
    the route won't 422 when called without some values. Provide sensible
    defaults to the template and only look up the user when a username is
    supplied.
    """
    users = load_users()
    user = users.get(username) if username else None

    # Ensure context has safe defaults
    ctx_package = package or "premium"
    ctx_price = price or 0
    ctx_quantity = quantity or 1
    total_price = ctx_price * ctx_quantity

    return templates.TemplateResponse(
        "premium-checkout.html",
        {
            "request": request,
            "username": username,
            "user": user,
            "package": ctx_package,
            "price": ctx_price,
            "quantity": ctx_quantity,
            "total": total_price,
        },
    )

@app.get("/coin-checkout", response_class=HTMLResponse)
def coin_checkout(request: Request, username: Optional[str] = None, package: Optional[str] = None, price: Optional[int] = 10000, quantity: Optional[int] = 1):
    """Render the xu checkout page. All query parameters are optional so
    the route won't 422 when called without some values. Provide sensible
    defaults to the template and only look up the user when a username is
    supplied.
    """
    users = load_users()
    user = users.get(username) if username else None

    # Ensure context has safe defaults
    ctx_package = package or "xu"
    ctx_price = price or 10000
    ctx_quantity = quantity or 1
    xu_per_pack = 2
    total_price = ctx_price * ctx_quantity
    total_xu = xu_per_pack * ctx_quantity
    # Provide a display name: prefer explicit username, else fall back to user record
    display_name = username or (user.get("username") if user and isinstance(user, dict) else None)

    return templates.TemplateResponse(
        "coin-checkout.html",
        {
            "request": request,
            "username": username,
            "display_name": display_name,
            "user": user,
            "package": ctx_package,
            "price": ctx_price,
            "quantity": ctx_quantity,
            "total": total_price,
            "xu_per_pack": xu_per_pack,
            "total_xu": total_xu,
        },
    )