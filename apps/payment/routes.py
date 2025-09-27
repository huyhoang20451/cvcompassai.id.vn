# Chứa API
from datetime import datetime
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Cookie, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlmodel import Session
from .services import get_client_ip, update_db_by_ResponseCode, update_order_status
from db import get_session
from Core.Auth.schemas import user
from .schemas import OrderSchema, OrderStatus
from Core.Auth.dependencies import templates, get_current_user, decode_token, authorize_role
from Core.OCR import run_vintern
from Core.config import settings
import uuid
from .dependencies import vnpay

router = APIRouter(tags=["payment"])

# Chuyển sang trang thanh toán của VNPAY
@router.post("/payment", response_class=RedirectResponse)
async def payment(request: Request, 
                  order_type: str = Form(...), 
                  amount_package: int = Form(...), 
                  package: str = Form(...),
                  user_info: user = Depends(authorize_role(["candidate","business"])),
                  session: Session = Depends(get_session)):

    ipaddr = get_client_ip(request)
    order_id = str(uuid.uuid4())

    # Tính tiền (ở đây giả định bạn có dict giá package)
    price_map = {
        "candidate_xu": 10000,
        "candidate_premium": 50000,
        "business_premium": 500000
    }
    if package not in price_map:
        raise HTTPException(status_code=400, detail="Invalid package type")

    total_money = amount_package * price_map[package]
    order_desc = f"{user_info.username} mua {amount_package} {package}"

    # Tạo OrderSchema từ dữ liệu form
    order = OrderSchema(
        id=str(uuid.uuid4()),              # sinh id
        user_id=user_info.id,
        package=package,
        amount=amount_package,
        total_money=amount_package,        # hoặc tính theo logic riêng
        description=order_type,
        status=OrderStatus.pending         # status mặc định
    )

    order = upsert_order_to_db(order, session)
    # 2. Tạo URL thanh toán
    vnp = vnpay()
    vnp.requestData = {
        "vnp_Version": "2.1.0",
        "vnp_Command": "pay",
        "vnp_TmnCode": "YOUR_TMN_CODE",
        "vnp_Amount": total_money * 100,   # VNPay tính theo đơn vị nhỏ nhất (VND * 100)
        "vnp_CurrCode": "VND",
        "vnp_TxnRef": order_id,
        "vnp_OrderInfo": order_desc,
        "vnp_OrderType": order_type,
        "vnp_Locale": "vn",
        "vnp_ReturnUrl": "https://yourdomain.com/payment_return",
        "vnp_IpAddr": ipaddr,
        "vnp_CreateDate": datetime.now().strftime("%Y%m%d%H%M%S"),
    }
    vnpay_payment_url = vnp.get_payment_url(settings.VNPAY_PAYMENT_URL, settings.VNPAY_HASH_SECRET_KEY)


    return RedirectResponse(url=vnpay_payment_url)

# VNPAY gửi request tới route này khi user thanh toán xong
@router.get("/payment_ipn")
async def payment_ipn(request: Request, session: Session = Depends(get_session)):
    input_data = dict(request.query_params)
    if not input_data:
        return JSONResponse({"RspCode": "99", "Message": "Invalid request"})

    vnp = vnpay()
    vnp.responseData = input_data

    order_id = input_data.get("vnp_TxnRef")
    vnp_ResponseCode = input_data.get("vnp_ResponseCode")

    # Validate chữ ký
    if not vnp.validate_response(settings.VNPAY_HASH_SECRET_KEY):
        return JSONResponse({"RspCode": "97", "Message": "Invalid Signature"})
    # Cập nhật DB dựa trên mã phản hồi
    order = update_db_by_ResponseCode(order_id, vnp_ResponseCode, session)
    return JSONResponse({"RspCode": "00", "Message": "Confirm Success"})

@router.get("/payment_return", response_class=HTMLResponse)
async def payment_return(request: Request):
    input_data = dict(request.query_params)
    context = {"request": request, "title": "Kết quả thanh toán"}

    if not input_data:
        context["result"] = ""
        return templates.TemplateResponse("payment_return.html", context)

    vnp = vnpay()
    vnp.responseData = input_data

    order_id = input_data.get("vnp_TxnRef")
    amount = int(input_data.get("vnp_Amount", 0)) / 100
    order_desc = input_data.get("vnp_OrderInfo")
    vnp_TransactionNo = input_data.get("vnp_TransactionNo")
    vnp_ResponseCode = input_data.get("vnp_ResponseCode")
    vnp_TmnCode = input_data.get("vnp_TmnCode")
    vnp_PayDate = input_data.get("vnp_PayDate")
    vnp_BankCode = input_data.get("vnp_BankCode")
    vnp_CardType = input_data.get("vnp_CardType")

    context.update({
        "order_id": order_id,
        "amount": amount,
        "order_desc": order_desc,
        "vnp_TransactionNo": vnp_TransactionNo,
        "vnp_ResponseCode": vnp_ResponseCode
    })

    if not vnp.validate_response(settings.VNPAY_HASH_SECRET_KEY):
        context["result"] = "Lỗi"
        context["msg"] = "Sai checksum"
        return templates.TemplateResponse("payment_return.html", context)

    if vnp_ResponseCode == "00":
        context["result"] = "Thành công"
    else:
        context["result"] = "Lỗi"

    return templates.TemplateResponse("payment_return.html", context)

