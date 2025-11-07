# Chứa API
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlmodel import Session
from .services import (get_orders, 
                       get_services, 
                       get_total_revenue,
                       count_orders,
                       count_users,
                       count_users_buy_packages,
                       sum_total_money_by_package,
                       failed_percentage,
                       get_users as service_get_users,
                       update_user as service_update_user,
                       delete_user_by_username,
                       update_service_by_id,
                       create_service as service_create_service,
                       delete_service_by_id as service_delete_service_by_id)
from db import get_session
from Core.Auth.dependencies import templates, authorize_role
from Core.Auth.schemas import user
from datetime import datetime, timezone
from typing import Optional
from Core.OCR import compare

router = APIRouter(tags=["admin"])

@router.get("/admin-dashboard", response_class=HTMLResponse)
async def read_root(request: Request, 
                    user_info: user = Depends(authorize_role(["admin"])),
                    session: Session = Depends(get_session)):
    total_revenue = get_total_revenue(session)
    total_orders = count_orders(session)
    total_users = count_users(session)
    package_stats = count_users_buy_packages(session)
    total_revenue_by_package = sum_total_money_by_package(session)
    failed_percentage_value = failed_percentage(session)
    return templates.TemplateResponse("admin_page.html", {
        "request": request, 
        "total_revenue": total_revenue, 
        "total_orders": total_orders, 
        "total_users": total_users, 
        "candidate_premium_users": package_stats.get("candidate_premium", 0),
        "candidate_xu_users": package_stats.get("candidate_xu", 0),
        "business_premium_users": package_stats.get("business_premium", 0),
        "total_users_buy_packages": sum(package_stats.values()),
        "total_revenue_business_premium": total_revenue_by_package.get("business_premium", 0),
        "total_revenue_candidate_premium": total_revenue_by_package.get("candidate_premium", 0),
        "total_revenue_candidate_xu": total_revenue_by_package.get("candidate_xu", 0),
        "failed_percentage": f"{failed_percentage_value:.2f}"
    })

@router.get("/users", response_class=HTMLResponse)
async def get_users(request: Request, 
                    session: Session = Depends(get_session)):
    users = service_get_users(session)
    return templates.TemplateResponse("users.html", {"request": request, "users": users})

@router.post("/update_user", response_class=JSONResponse)
async def update_user(username: str = Form(...),
                      password: str = Form(...),
                      role: str = Form(...),
                      coin: str = Form(...),
                      premium_expires: str = Form(...),
                      session: Session = Depends(get_session)):

    if premium_expires == "None":
        premium_expires = None

    user = service_update_user(session, 
                       username, 
                       password, 
                       role, 
                       int(coin), 
                       premium_expires)
    if not user:
        return JSONResponse(status_code=404, content={"message": "User not found"})
    return RedirectResponse(url="/users", status_code=303)

@router.post("/delete_user/{username}", response_class=JSONResponse)
async def delete_user(username: str,
                      session: Session = Depends(get_session)):
    result = delete_user_by_username(session, username)
    return RedirectResponse(url="/users", status_code=303)

# Lấy danh sách dịch vụ
@router.get("/services", response_class=HTMLResponse)
def services(request: Request, 
             session: Session = Depends(get_session)):
    service_list = get_services(session)
    return templates.TemplateResponse("services.html", {"request": request, "services": service_list})

# Tạo dịch vụ mới
@router.post("/services", response_class=HTMLResponse)
def create_service(request: Request,
                   name: str = Form(...),
                   description: str = Form(...),
                   price: float = Form(...),
                   session: Session = Depends(get_session)):
    print("Creating service:", name, description, price)
    service = service_create_service(session, name, description, price)
    return RedirectResponse(url="/services", status_code=303)

# Cập nhật dịch vụ
@router.patch("/services/{service_id}", response_class=HTMLResponse)
def update_service(request: Request,
                   service_id: int,
                   name: Optional[str] = Form(None),
                   description: Optional[str] = Form(None),
                   price: Optional[int] = Form(None),
                   session: Session = Depends(get_session)):
    service_list = update_service_by_id(session, service_id, name, description, price)
    return templates.TemplateResponse("services.html", {"request": request, "services": service_list})

# Xoá dịch vụ
@router.post("/services/delete/{service_id}", response_class=HTMLResponse)
def delete_service(service_id: int,
                   session: Session = Depends(get_session)):
    result = service_delete_service_by_id(session, service_id)
    return RedirectResponse(url="/services", status_code=303)

@router.get("/quality-cv-checker", response_class=HTMLResponse)
def quality_cv_checker(request: Request):
    return templates.TemplateResponse("cv-scan-quality-manage.html", {"request": request})

@router.get("/transaction-manage", response_class=HTMLResponse)
def transaction_manage(request: Request, 
                       session: Session = Depends(get_session)):
    order_list = get_orders(session)
    return templates.TemplateResponse("transaction-manage.html", {"request": request, "orders": order_list})