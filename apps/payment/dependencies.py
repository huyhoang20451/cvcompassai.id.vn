
# from payos import PayOS, ItemData, PaymentData
# from Core.config import settings

# client_id = settings.PAYOS_CLIENT_ID
# api_key = settings.PAYOS_API_KEY
# checksum_key = settings.PAYOS_CHECKSUM_KEY

# payOS = PayOS(client_id=client_id, api_key=api_key, checksum_key=checksum_key)

# # Truyền thông tin đơn hàng để tạo link thanh toán
# item = ItemData(name="Mì tôm hảo hảo ly", quantity=1, price=1000)

# paymentData = PaymentData(orderCode=11, amount=1000, description="Thanh toan don hang",
#      items=[item], cancelUrl="http://localhost:8000", returnUrl="http://localhost:8000")

# paymentLinkData = payOS.createPaymentLink(paymentData = paymentData)

#from payos import PayOS, ItemData, PaymentData
#from Core.config import settings
#
#client_id = settings.PAYOS_CLIENT_ID
#api_key = settings.PAYOS_API_KEY
#checksum_key = settings.PAYOS_CHECKSUM_KEY
#
#payOS = PayOS(client_id=client_id, api_key=api_key, checksum_key=checksum_key)
#
## Truyền thông tin đơn hàng để tạo link thanh toán
#item = ItemData(name="Mì tôm hảo hảo ly", quantity=1, price=1000)
#
#paymentData = PaymentData(orderCode=11, amount=1000, description="Thanh toan don hang",
#     items=[item], cancelUrl="http://localhost:8000", returnUrl="http://localhost:8000")
#
#paymentLinkData = payOS.createPaymentLink(paymentData = paymentData)

