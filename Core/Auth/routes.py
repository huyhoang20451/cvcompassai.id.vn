from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from .services import (authenticate_user, 
                       create_access_token, 
                       create_user, 
                       login_for_access_token,
                       get_user_by_username)
from sqlmodel import Session
from .schemas import Token, UserCreate, Login_form
from ..config import settings
from datetime import timedelta
from db import get_session
from .dependencies import templates, decode_token

router = APIRouter(tags=["auth"])


# Trang đăng nhập
@router.get("/login", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

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
    if role == "business":
        url = f"/business-dashboard"
    else:
        url = f"/home-logged-in"
    response = RedirectResponse(url=url, status_code=303)
    response.set_cookie(
        key="access_token",        # tên cookie
        value=token.access_token,  # token bạn vừa tạo
        httponly=True,             # chỉ truy cập được từ HTTP, không JS
        max_age=3600               # thời gian sống cookie, tùy chỉnh
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
    user_in = UserCreate(**form_data)  # parse sang Pydantic model
    new_user = create_user(session, 
                           user_in.username, 
                           user_in.password,
                           user_in.role,
                           user_in.company_name)
    if not new_user:
        raise templates.TemplateResponse("register.html", {"request": request, "error": "Tên người dùng đã tồn tại"})
    return templates.TemplateResponse("login.html", {"request": request, "success": "Đăng ký thành công"})

# Đăng xuất
@router.get("/logout", response_class=RedirectResponse)
async def register_page(request: Request):
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="access_token", httponly=True)
    return response
