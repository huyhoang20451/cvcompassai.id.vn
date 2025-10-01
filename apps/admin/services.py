from sqlmodel import Session
from .repository import (get_paid_orders as repo_get_paid_orders,
                         count_orders as repo_count_orders,
                         count_users as repo_count_users,
                         count_users_by_package as repo_count_users_by_package,
                         sum_total_money_by_package as repo_sum_total_money_by_package,
                         failed_percentage as repo_failed_percentage,
                         get_users as repo_get_users,
                         update_user_by_username as repo_update_user_by_username,
                         delete_user_by_username as repo_delete_user_by_username,
                         get_services as repo_get_services,
                         get_orders as repo_get_orders)
from fastapi import Depends
from typing import Annotated, List
from .schemas import OrderSchema, Service, user
from Core.Auth.dependencies import get_current_user
from Core.OCR import compare
from Core.Auth.hashing import get_password_hash

# Tổng doanh thu từ các đơn đã thanh toán
def get_total_revenue(session: Session) -> int:
    paid_orders = repo_get_paid_orders(session)
    total_revenue = sum(order.total_money for order in paid_orders)
    return total_revenue

# Đếm số lượng đơn hàng
def count_orders(session: Session) -> int:
    return repo_count_orders(session)

# Đếm số lượng người dùng
def count_users(session: Session) -> int:
    return repo_count_users(session)

# Đếm số lượng người dùng đã mua từng loại gói
def count_users_buy_packages(session: Session) -> dict:
    return repo_count_users_by_package(session)

# Tổng tiền thu được cho từng package
def sum_total_money_by_package(session: Session) -> dict:
    return repo_sum_total_money_by_package(session)

# Tỷ lệ phần trăm đơn hàng bị hủy
def failed_percentage(session: Session) -> float:
    return repo_failed_percentage(session)

# Lấy thông tin tất cả user
def get_users(session: Session) -> List[user]:
    return repo_get_users(session)

# Câp nhật thông tin user
def update_user(session: Session, 
                username: str, 
                password: str, 
                role: str, 
                coin: int, 
                premium_expires: str):
    hashed_password = get_password_hash(password)
    user = repo_update_user_by_username(session, 
                                        username, 
                                        hashed_password, 
                                        coin, 
                                        premium_expires)
    return user

# Xoá user theo username
def delete_user_by_username(session: Session, username: str) -> bool:
    return repo_delete_user_by_username(session, username)

def get_services(session: Session) -> List[Service]:
    return repo_get_services(session)

def get_orders(session: Session) -> List[OrderSchema]:
    return repo_get_orders(session)