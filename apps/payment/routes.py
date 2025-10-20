# Chứa API
from datetime import datetime
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Cookie, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlmodel import Session
from .services import (update_db_by_ResponseCode, 
                       create_order_to_db,
                       get_package_info_by_name,
                       create_paymentData)
from db import get_session
from Core.Auth.schemas import user
from .schemas import OrderSchema, OrderStatus, pricemap
from Core.Auth.dependencies import templates, get_current_user, decode_token, authorize_role
from Core.OCR import run_vintern
from Core.config import settings
import uuid
from .dependencies import payOS
from Core.Auth.services import get_user_by_username
from payos import ItemData, PaymentData

router = APIRouter(tags=["payment"])

# Chuyển sang trang thanh toán của payOS
@router.post("/payment", response_class=RedirectResponse)
async def payment(request: Request, 
                  package: str = Form(...), # tên gói dịch vụ
                  amount_package: int = Form(...),
                  user_info: user = Depends(authorize_role(["candidate","business"])),
                  session: Session = Depends(get_session)):

    price = get_package_info_by_name(package, session).price
    total_money = amount_package * price
    order_desc = f"{user_info.id}"



    # Tạo OrderSchema từ dữ liệu form
    order = OrderSchema(
        id=str(uuid.uuid4()),              # sinh id
        user_id=user_info.id,
        package=package,
        amount=amount_package,
        total_money=total_money,
        description=order_desc,
        status=OrderStatus.pending         # status mặc định
    )

    order = create_order_to_db(order, session)
    if user_info.role == "candidate":
        url = "https://cvcompas.ngrok.app/home-logged-in"
    else:
        url = "https://cvcompas.ngrok.app/business-dashboard"

    payment_data = create_paymentData(
        order_id=order.id,
        name=order.description,
        amount=order.amount,
        total_money=order.total_money,
        price=order.total_money,
        description=order.description,
        return_url=url,
        cancel_url=url
    )

    result = payOS.createPaymentLink(paymentData=payment_data)

    return RedirectResponse(url=result.checkoutUrl)


# payOS gọi về đây
@router.post("/webhook", response_class=JSONResponse)
async def payment_ipn(request: Request,
                      session: Session = Depends(get_session)):
    body = await request.json()
    if not body:
        return JSONResponse({"RspCode": "99", "Message": "Invalid request"})
    
    webhookData = payOS.verifyPaymentWebhookData(body)
    if not webhookData:
        return JSONResponse({"RspCode": "97", "Message": "Invalid signature"})
    
    # Cập nhật DB dựa trên mã phản hồi
    order = update_db_by_ResponseCode(webhookData.description, webhookData.orderCode, webhookData.code, session)

    if order.status == OrderStatus.paid:
        return JSONResponse({"RspCode": "00", "Message": "Success"})
    else:
        return JSONResponse({"RspCode": "01", "Message": "Giao dịch không thành công"})
