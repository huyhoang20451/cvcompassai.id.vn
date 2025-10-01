# Chứa API
#from datetime import datetime
#from typing import Annotated, List, Optional
#from fastapi import APIRouter, Depends, HTTPException, Request, Cookie, File, UploadFile, Form
#from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
#from sqlmodel import Session
#from .services import get_client_ip, update_db_by_ResponseCode, create_order_to_db
#from db import get_session
#from Core.Auth.schemas import user
#from .schemas import OrderSchema, OrderStatus, pricemap
#from Core.Auth.dependencies import templates, get_current_user, decode_token, authorize_role
#from Core.OCR import run_vintern
#from Core.config import settings
#import uuid
#from .dependencies import vnpay
#from Core.Auth.services import get_user_by_username
#
#router = APIRouter(tags=["payment"])
#
## Chuyển sang trang thanh toán của VNPAY
#@router.post("/payment", response_class=RedirectResponse)
#async def payment(request: Request, 
#                  order_type: str = Form(...), 
#                  amount_package: int = Form(...), 
#                  package: str = Form(...),
#                  user_info: user = Depends(authorize_role(["candidate","business"])),
#                  session: Session = Depends(get_session)):
#
#    ipaddr = get_client_ip(request)
#    order_id = str(uuid.uuid4())
#
#
#    if package not in pricemap.__members__:
#        raise HTTPException(status_code=400, detail="Invalid package type")
#
#    total_money = amount_package * pricemap[package].value
#    order_desc = f"{user_info.username} mua {amount_package} {package}"
#
#    # Tạo OrderSchema từ dữ liệu form
#    order = OrderSchema(
#        id=str(uuid.uuid4()),              # sinh id
#        user_id=user_info.id,
#        package=package,
#        amount=amount_package,
#        total_money=amount_package,        # hoặc tính theo logic riêng
#        description=order_type,
#        status=OrderStatus.pending         # status mặc định
#    )
#
#    order = create_order_to_db(order, session)
#    # 2. Tạo URL thanh toán
#    vnp = vnpay()
#    vnp.requestData = {
#        "vnp_Version": "2.1.0",
#        "vnp_Command": "pay",
#        "vnp_TmnCode": "YOUR_TMN_CODE",
#        "vnp_Amount": total_money * 100,   # VNPay tính theo đơn vị nhỏ nhất (VND * 100)
#        "vnp_CurrCode": "VND",
#        "vnp_TxnRef": order_id,
#        "vnp_OrderInfo": order_desc,
#        "vnp_OrderType": order_type,
#        "vnp_Locale": "vn",
#        "vnp_ReturnUrl": "https://yourdomain.com/payment_return",
#        "vnp_IpAddr": ipaddr,
#        "vnp_CreateDate": datetime.now().strftime("%Y%m%d%H%M%S"),
#    }
#    vnpay_payment_url = vnp.get_payment_url(settings.VNPAY_PAYMENT_URL, settings.VNPAY_HASH_SECRET_KEY)
#
#
#    return RedirectResponse(url=vnpay_payment_url)
#
## VNPAY gửi request tới route này khi user thanh toán xong
#@router.get("/payment_ipn")
#async def payment_ipn(request: Request, session: Session = Depends(get_session)):
#    input_data = dict(request.query_params)
#    if not input_data:
#        return JSONResponse({"RspCode": "99", "Message": "Invalid request"})
#
#    vnp = vnpay()
#    vnp.responseData = input_data
#
#    order_id = input_data.get("vnp_TxnRef")
#    vnp_ResponseCode = input_data.get("vnp_ResponseCode")
#
#    # Validate chữ ký
#    if not vnp.validate_response(settings.VNPAY_HASH_SECRET_KEY):
#        return JSONResponse({"RspCode": "97", "Message": "Invalid Signature"})
#    # Cập nhật DB dựa trên mã phản hồi
#    order = update_db_by_ResponseCode(order_id, vnp_ResponseCode, session)
#    return JSONResponse({"RspCode": "00", "Message": "Confirm Success"})
#
## User được chuyển về đây sau khi thanh toán xong
#@router.get("/payment_return", response_class=HTMLResponse)
#async def payment_return(request: Request,
#                         session: Session = Depends(get_session)):
#    input_data = dict(request.query_params)
#
#    if not input_data:
#        return templates.TemplateResponse("payment_return.html")
#
#    vnp = vnpay()
#    vnp.responseData = input_data
#
#    order_id = input_data.get("vnp_TxnRef")
#    amount = int(input_data.get("vnp_Amount", 0)) / 100
#    order_desc = input_data.get("vnp_OrderInfo")
#    vnp_ResponseCode = input_data.get("vnp_ResponseCode")
#    parts = order_desc.split()
#
#    username = parts[0]
#    amount_package = int(parts[2])
#    package = parts[3]
#
#    user_info = get_user_by_username(session, username)
#    if not vnp.validate_response(settings.VNPAY_HASH_SECRET_KEY):
#        return templates.TemplateResponse("payment_return.html")
#
#    # Tính xu nhận được
#    if package == "candidate_xu":
#        coins_received = amount_package*2
#    elif package == "candidate_premium":
#        coins_received = 5
#    else:
#        coins_received = None
#
#    if vnp_ResponseCode == "00":
#        return templates.TemplateResponse("success-transaction.html", {"request": request, 
#                                                                       "amount": amount, 
#                                                                       "order_id": order_id, 
#                                                                       "message": "Giao dịch thành công", 
#                                                                       "coins_received": coins_received, 
#                                                                       "new_balance": user_info.coin + (coins_received if coins_received else 0), 
#                                                                       "username": username})
#    else:
#        return templates.TemplateResponse("fail-transaction.html", {"request": request, 
#                                                                    "message": "Giao dịch không thành công",})
#