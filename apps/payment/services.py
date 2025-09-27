from fastapi import APIRouter, Form, Request, Depends, HTTPException
from starlette.responses import RedirectResponse
from datetime import datetime
from Core.config import settings
from .dependencies import vnpay
from .schemas import OrderSchema, OrderStatus
from .repository import (create_order as repo_create_order,
                         get_order as repo_get_order,
                         update_user_role as repo_update_user_role,
                         update_order_status as repo_update_order_status)
from apps.candidate.repository import update_coin as repo_update_coin
from Core.Auth.services import get_user_by_id
from sqlmodel import Session

# Lấy IP của client
def get_client_ip(request: Request):
    """Lấy IP thật của client"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ip = forwarded.split(",")[0]
    else:
        ip = request.client.host
    return ip

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

    price_map = {
        "candidate_xu": 10000,
        "candidate_premium": 50000,
        "business_premium": 500000
    }

    if order.status == OrderStatus.paid:
        if order.package == "candidate_xu":
            xu = 2*(order.total_money // price_map["candidate_xu"])
            update_user_coin(order.user_id, user.coin + xu)
        elif order.package == "candidate_premium":
            update_user_coin(order.user_id, user.coin + 5)
            update_user_role(order.user_id, "candidate_premium")
        elif order.package == "business_premium":
            update_user_role(order.user_id, "business_premium")
    return order


# Cài đặt Code Return URL
def payment_return(request): 
    inputData = request.GET
    if inputData:
        vnp = vnpay()
        vnp.responseData = inputData.dict()
        order_id = inputData['vnp_TxnRef']
        amount = int(inputData['vnp_Amount']) / 100
        order_desc = inputData['vnp_OrderInfo']
        vnp_TransactionNo = inputData['vnp_TransactionNo']
        vnp_ResponseCode = inputData['vnp_ResponseCode']
        vnp_TmnCode = inputData['vnp_TmnCode']
        vnp_PayDate = inputData['vnp_PayDate']
        vnp_BankCode = inputData['vnp_BankCode']
        vnp_CardType = inputData['vnp_CardType']
        if vnp.validate_response(settings.VNPAY_HASH_SECRET_KEY):
            if vnp_ResponseCode == "00":
                return render(request, "payment_return.html", {"title": "Kết quả thanh toán",
                                                               "result": "Thành công", "order_id": order_id,
                                                               "amount": amount,
                                                               "order_desc": order_desc,
                                                               "vnp_TransactionNo": vnp_TransactionNo,
                                                               "vnp_ResponseCode": vnp_ResponseCode})
            else:
                return render(request, "payment_return.html", {"title": "Kết quả thanh toán",
                                                               "result": "Lỗi", "order_id": order_id,
                                                               "amount": amount,
                                                               "order_desc": order_desc,
                                                               "vnp_TransactionNo": vnp_TransactionNo,
                                                               "vnp_ResponseCode": vnp_ResponseCode})
        else:
            return render(request, "payment_return.html",
                          {"title": "Kết quả thanh toán", "result": "Lỗi", "order_id": order_id, "amount": amount,
                           "order_desc": order_desc, "vnp_TransactionNo": vnp_TransactionNo,
                           "vnp_ResponseCode": vnp_ResponseCode, "msg": "Sai checksum"})
    else:
        return render(request, "payment_return.html", {"title": "Kết quả thanh toán", "result": ""})
           
           