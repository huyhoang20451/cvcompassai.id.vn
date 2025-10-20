from fastapi import APIRouter, Form, Request, Depends, HTTPException
from starlette.responses import RedirectResponse
from datetime import datetime, timedelta
from Core.config import settings
from .dependencies import vnpay
from .schemas import OrderSchema, OrderStatus, pricemap
from .repository import (create_order as repo_create_order,
                         get_order as repo_get_order,
                         update_user_role as repo_update_user_role,
                         update_order_status as repo_update_order_status,
                         update_user_expires_premium as repo_update_user_expires_premium,
                         get_package_info_by_name as repo_get_package_info_by_name)
from apps.candidate.repository import update_coin as repo_update_coin
from Core.Auth.services import get_user_by_id
from sqlmodel import Session
from payos import PayOS, ItemData, PaymentData

# Thêm hoặc cập nhật order trong DB
def create_order_to_db(order: OrderSchema, session: Session) -> OrderSchema:
    return repo_create_order(order, session)

# Lấy order theo id
def get_order(id: int, session: Session) -> OrderSchema:
    return repo_get_order(id, session)

# Cập nhật role cho user
def update_user_role(user_id: int, new_role: str):
    return repo_update_user_role(user_id, new_role)

# Cập nhật coin cho user
def update_user_coin(username: str, coin: int):
    return repo_update_coin(username, coin)

# Cập nhật theo trạng thái trả về từ VNPAY
# Candidate_xu: cập nhật coin, cập nhật trạng thái order, không đổi role
# Candidate_premium: cập nhật coin, cập nhật trạng thái order, đổi role
# Business_premium: không cập nhật coin, cập nhật trạng thái order, đổi role
def update_order_status(order_id: str, new_status: str, session: Session) -> OrderSchema:
    order = repo_update_order_status(order_id, new_status, session)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

def update_db_by_ResponseCode(user_id, order_id, response_code, session: Session):
    order = get_order(order_id, session)
    user = get_user_by_id(session, user_id)
    # Cập nhật status đơn hàng dựa trên mã phản hồi
    if response_code == "00":
        order = update_order_status(order_id, OrderStatus.paid, session)
    else:
        order = update_order_status(order_id, OrderStatus.failed, session)

    today = datetime.now().date()
    new_expires = today + timedelta(days=30)

    if order.status == OrderStatus.paid:
        if order.package == "candidate_xu":
            xu = 2*(order.total_money // pricemap.candidate_xu.value)

            update_user_coin(order.user_id, user.coin + xu)
        elif order.package == "candidate_premium":
            update_user_coin(order.user_id, user.coin + 5)
            update_user_role(order.user_id, "candidate_premium")
            repo_update_user_expires_premium(order.user_id, new_expires, session)
            
        elif order.package == "business_premium":
            update_user_role(order.user_id, "business_premium")
            repo_update_user_expires_premium(order.user_id, new_expires, session)
    return order

def get_package_info_by_name(package_name: str, session: Session):
    return repo_get_package_info_by_name(package_name, session)

def create_paymentData(order_id: str, 
                       name: str, 
                       amount: int, 
                       total_money: int, 
                       price: int, 
                       description: str, 
                       return_url: str, 
                       cancel_url: str):
    item = ItemData(name=name, quantity=amount, price=price)
    payment_data = PaymentData(
        orderCode= order_id,
        amount=total_money,
        description=description,
        items=[item],
        cancelUrl=cancel_url,
        returnUrl=return_url
    )
    return payment_data
