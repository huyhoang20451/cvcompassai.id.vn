from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, requests, status, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from .services import (authenticate_user, 
                       create_access_token, 
                       create_user, 
                       login_for_access_token,
                       get_user_by_username,
                       get_user_by_google_id)
from sqlmodel import Session
from .schemas import Token, CandidateCreate, BusinessCreate, Login_form
from ..config import settings
from datetime import timedelta
from db import get_session
from .dependencies import templates, decode_token
from google.oauth2 import id_token
from google.auth.transport import requests

router = APIRouter(tags=["auth"])


# Trang đăng nhập
@router.get("/login", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request,
                                                     "google_client_id": settings.GOOGLE_CLIENT_ID})

# Đăng nhập
@router.post("/login", response_class=HTMLResponse)
async def register_page(request: Request, session: Session = Depends(get_session)):
    form = await request.form()
    login_form = dict(form)
    login_form = Login_form(**login_form)  # parse sang Pydantic model
    token = login_for_access_token(login_form, 
                                   session)
    if not token:
        raise HTTPException(status_code=400, detail="Sai username hoặc password")
    username, role, company_name = decode_token(token.access_token)
    print(username, role, company_name)
    if role in ["business", "business_premium"]:
        url = f"/business-dashboard"
    elif role in ["candidate", "candidate_premium"]:
        url = f"/home-logged-in"
    else:
        url = f"/admin-dashboard"
    
    response = RedirectResponse(url=url, status_code=303)
    response.set_cookie(
        key="access_token",        # tên cookie
        value=token.access_token,  # token bạn vừa tạo
        httponly=True,             # chỉ truy cập được từ HTTP, không JS
        max_age=3600               # thời gian sống cookie, tùy chỉnh
    )
    return response

@router.post("/google-login", response_class=HTMLResponse)
async def google_login(request: Request, 
                       session: Session = Depends(get_session)):
    data = await request.json()
    print(data)
    id_token_str = data.get("id_token")

    if not id_token_str:
        raise HTTPException(status_code=400, detail="Thiếu Google ID token")

    try:
        # 1️⃣ Xác minh token Google
        idinfo = id_token.verify_oauth2_token(
            id_token_str, requests.Request()
        )

        email = idinfo["email"]
        name = idinfo.get("name", "")
        google_id = idinfo["sub"]  # ID duy nhất của người dùng trong Google
        print(f"Google ID: {google_id}, Email: {email}, Name: {name}")
    except ValueError:
        raise HTTPException(status_code=401, detail="Token Google không hợp lệ")
    
    role = data.get("role")
    company_name = data.get("company_name", None)
    user = get_user_by_google_id(session, google_id)
    if not user:
        if not role:
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "error_message": "⚠️ Vai trò (role) không được để trống!"}
            )
    # Đăng ký
    if not user:
        try:
            if role == "candidate":
                user_in = CandidateCreate(username=name, email=email, role=role, full_name=name)
            elif role == "business":
                user_in = BusinessCreate(username=name, email=email, role=role, company_name=company_name)
            else:
                raise ValueError("Vai trò không hợp lệ")
            print(f"Registering new user: {user_in}")
            new_user = create_user(session,
                                username=user_in.username,
                                password=user_in.password,
                                email=user_in.email,
                                role=user_in.role,
                                company_name=getattr(user_in, "company_name", None),
                                full_name=getattr(user_in, "full_name", None),
                                google_id=google_id)
            print(f"New user created: {new_user}")
        except Exception as e:
            return JSONResponse(status_code=400, content={"detail": f"Lỗi đăng ký: {e}"})
        # 4️⃣ Tạo JWT riêng của bạn
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub" : user_in.username, "role": user_in.role, "company_name": getattr(user_in, "company_name", None)},
                                            expires_delta=access_token_expires)
    else:
        # 4️⃣ Tạo JWT riêng của bạn
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub" : user.username, "role": user.role, "company_name": user.company_name},
                                            expires_delta=access_token_expires)
    print("Access Token:", access_token)
    username, role, company_name = decode_token(access_token)
    print(username, role, company_name)
    # 5️⃣ Điều hướng theo role
    if role in ["business", "business_premium"]:
        url = "/business-dashboard"
    elif role in ["candidate", "candidate_premium"]:
        url = "/home-logged-in"
    else:
        url = "/admin-dashboard"

    # 6️⃣ Gửi cookie chứa JWT
    response = RedirectResponse(url=url, status_code=303)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=3600
    )
    return response

    
# Trang đăng ký:
@router.get("/signup", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


# Đăng ký
@router.post("/signup", response_class=HTMLResponse)
async def register(request: Request, session: Session = Depends(get_session)):
    form = await request.form()
    form_data = dict(form)
    print(form_data)
    role = form_data.get("role")
    print(role)
    try:
        if role == "candidate":
            user_in = CandidateCreate(**form_data)
        elif role == "business":
            user_in = BusinessCreate(**form_data)
        else:
            raise ValueError("Vai trò không hợp lệ")
    except Exception as e:
        return templates.TemplateResponse(
            "register.html", {"request": request, 
                              "error": f"Dữ liệu không hợp lệ: {e}"})
    new_user = create_user(session,
                           username=user_in.username,
                           password=user_in.password,
                           email=user_in.email,
                           role=user_in.role,
                           company_name=getattr(user_in, "company_name", None),
                           full_name=getattr(user_in, "full_name", None))
    if not new_user:
        raise templates.TemplateResponse("register.html", {"request": request, "error": "Tên người dùng đã tồn tại"})
    return templates.TemplateResponse("login.html", {"request": request, "success": "Đăng ký thành công"})

# Đăng xuất
@router.get("/logout", response_class=RedirectResponse)
async def register_page(request: Request):
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="access_token", httponly=True)
    return response
