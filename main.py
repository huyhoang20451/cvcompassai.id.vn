from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from apps.candidate.routes import router as candidate_router
from apps.business.routes import router as business_router
from apps.setting.routes import router as setting_router
from apps.admin.routes import router as admin_router
from apps.payment.routes import router as payment_router
from Core.Auth.routes import router as auth_router
from Core.Auth.dependencies import authorize_role, templates
from Core.Auth.schemas import user
from db import init_db, get_session
from sqlmodel import Session

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Đăng ký router của từng module
app.include_router(auth_router)
app.include_router(candidate_router)
app.include_router(business_router)
app.include_router(setting_router)
app.include_router(admin_router)
app.include_router(payment_router)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/items/", response_model=None)
async def read_items(user = Depends(authorize_role(["admin"]))):
    return ("authorized")

# Trang chủ
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/about-us")
async def about_us(request: Request):
    return templates.TemplateResponse("about-us.html", {"request": request})

@app.get("/pricing", response_class=HTMLResponse)
def pricing(request: Request):
    return templates.TemplateResponse("pricing.html", {"request": request})

@app.get("/edit-profile", response_class=HTMLResponse)
def edit_profile(request: Request,
                 user_info: user = Depends(authorize_role(["candidate", "business", "candidate_premium", "business_premium"]))):

    return templates.TemplateResponse("settings.html", {"request": request, "user_info": user_info})

@app.get("/system-settings", response_class=HTMLResponse)
def system_settings(request: Request,
                    user_info: user = Depends(authorize_role(["candidate", "business", "candidate_premium", "business_premium"]))):
    return templates.TemplateResponse("system-settings.html", {"request": request, "user_info": user_info})
