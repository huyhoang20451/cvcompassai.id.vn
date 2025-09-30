import json
import os
import math
from fastapi import FastAPI, HTTPException, Form, Request, requests
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from flask import request
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta

from htmlbackend import load_users

app = FastAPI()

class User(BaseModel):
    id: str
    username: str
    password: str
    role: str
    coin: int
    premium_expires: Optional[str] = None

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="admin_pages")

# Hàm lấy các số liệu từ file JSON
def get_totalrevenue_from_json():
    # Mở file orders.json và đọc dữ liệu
    with open('database/orders.json', 'r', encoding='utf-8') as file:
        orders = json.load(file)
    # Tính tổng doanh thu (ưu tiên key 'amount', fallback 'total_price')
    total_revenue = 0
    if isinstance(orders, dict):
        order_list = orders.values()
    else:
        order_list = orders
    for order in order_list:
        val = order.get('amount') or order.get('total_price')
        # lọc ra trạng thái là paid
        if order.get('status') == 'paid':
            try:
                total_revenue += int(val)
            except (TypeError, ValueError):
                continue
    return total_revenue

# Đếm số lượng đơn hàng từ file JSON
def count_orders_from_json():
    with open('database/orders.json', 'r', encoding='utf-8') as file:
        orders = json.load(file)
    if isinstance(orders, dict):
        return len(orders)
    elif isinstance(orders, list):
        return len(orders)
    return 0

def count_users():
    users = load_users()
    # chỉ đếm vai trò là user
    return len([user for user in users if user['role'] == 'user'])

def count_users_buy_packages():
    # Đếm số đơn hàng đã mua gói premium và xu từ orders.json
    # Đếm tất cả orders, không gộp theo username
    with open('database/orders.json', 'r', encoding='utf-8') as file:
        orders = json.load(file)
        premium_orders = 0
        coin_orders = 0
        if isinstance(orders, dict):
            order_list = orders.values()
        else:
            order_list = orders
        for order in order_list:
            if isinstance(order, dict) and order.get('status') == 'paid':
                package = order.get('package')
                
                # Có trường package và là premium
                if package == 'premium':
                    premium_orders += 1
                # Có trường package và là xu/coin
                elif package == 'xu' or package == 'coin':
                    coin_orders += 1
                # Không có package (orders cũ) → coi như mua xu
                elif package is None:
                    coin_orders += 1
        
        return {
            "premium_users": premium_orders,
            "coin_users": coin_orders, 
            "total_users": premium_orders + coin_orders
        }

def total_amount_from_orders_by_package(package_name):
    with open('database/orders.json', 'r', encoding='utf-8') as file:
        orders = json.load(file)
    total_amount = 0
    if isinstance(orders, dict):
        order_list = orders.values()
    else:
        order_list = orders
    for order in order_list:
        if isinstance(order, dict) and order.get('status') == 'paid':
            val = order.get('amount') or order.get('total_price')
            try:
                amount = int(val)
                package = order.get('package')
                
                # Nếu có trường package, dùng theo package
                if package == package_name:
                    total_amount += amount
                # Nếu không có package và tìm xu/coin, coi như là xu (orders cũ)
                elif package is None and package_name == "xu":
                    total_amount += amount
                # Nếu package khác với package_name thì bỏ qua
                    
            except (TypeError, ValueError):
                continue
    return total_amount

def cancelled_percentage():
    with open('database/orders.json', 'r', encoding='utf-8') as file:
        orders = json.load(file)
    total_orders = 0
    cancelled_orders = 0
    if isinstance(orders, dict):
        order_list = orders.values()
    else:
        order_list = orders
    for order in order_list:
        if isinstance(order, dict):
            total_orders += 1
            if order.get('status') == 'cancelled':
                cancelled_orders += 1
    if total_orders == 0:
        return 0
    return (cancelled_orders / total_orders) * 100

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    total_revenue = get_totalrevenue_from_json()
    total_orders = count_orders_from_json()
    total_users = count_users()
    package_stats = count_users_buy_packages()
    total_revenue_premium = total_amount_from_orders_by_package("premium")
    total_revenue_coin = total_amount_from_orders_by_package("xu")
    cancelled_percentage_value = cancelled_percentage()
    return templates.TemplateResponse("admin_page.html", {
        "request": request, 
        "total_revenue": total_revenue, 
        "total_orders": total_orders, 
        "total_users": total_users, 
        "premium_users": package_stats["premium_users"],
        "coin_users": package_stats["coin_users"],
        "total_users_buy_packages": package_stats["total_users"],
        "total_revenue_premium": total_revenue_premium,
        "total_revenue_coin": total_revenue_coin,
        "cancelled_percentage": f"{cancelled_percentage_value:.2f}"
    })


@app.get("/users", response_class=HTMLResponse)
async def get_users(request: Request):
    with open('database/users.json', 'r', encoding='utf-8') as file:
        users = json.load(file)
    if isinstance(users, dict):
        user_list = list(users.values())
    else:
        user_list = users
    return templates.TemplateResponse("users.html", {"request": request, "users": user_list})

def load_users():
    with open('database/users.json', 'r', encoding='utf-8') as file:
        users = json.load(file)
    if isinstance(users, dict):
        return list(users.values())
    return users

def save_users(users):
    with open('database/users.json', 'w', encoding='utf-8') as file:
        json.dump(users, file, indent=4, ensure_ascii=False)

@app.post("/update_user", response_class=JSONResponse)
async def update_user(
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    coin: str = Form(...),
    premium_expires: str = Form(...),
):
    users = load_users()
    user_found = False
    for user in users:
        if user['username'] == username:
            user['username'] = username
            user['password'] = password
            user['role'] = role
            try:
                user['coin'] = int(coin)
            except ValueError:
                user['coin'] = coin
            user['premium_expires'] = premium_expires if premium_expires else None
            user_found = True
            break
    if not user_found:
        return JSONResponse(status_code=404, content={"message": "User not found"})
    save_users(users)
    return RedirectResponse(url="/users", status_code=303)

@app.post("/delete_user/{username}", response_class=JSONResponse)
async def delete_user(username: str):
    users = load_users()
    users = [user for user in users if user['username'] != username]
    save_users(users)
    return RedirectResponse(url="/users", status_code=303)

@app.get("/services", response_class=HTMLResponse)
def services(request: Request):
    with open('database/services.json', 'r', encoding='utf-8') as file:
        services = json.load(file)
    if isinstance(services, dict):
        service_list = list(services.values())
    else:
        service_list = services
    return templates.TemplateResponse("services.html", {"request": request, "services": service_list})

@app.get("/quality-cv-checker", response_class=HTMLResponse)
def quality_cv_checker(request: Request):
    return templates.TemplateResponse("cv-scan-quality-manage.html", {"request": request})

@app.get("/transaction-manage", response_class=HTMLResponse)
def transaction_manage(request: Request):
    with open('database/orders.json', 'r', encoding='utf-8') as file:
        orders = json.load(file)
    if isinstance(orders, dict):
        order_list = list(orders.values())
    else:
        order_list = orders
    return templates.TemplateResponse("transaction-manage.html", {"request": request, "orders": order_list})