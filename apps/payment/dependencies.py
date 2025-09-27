import hashlib
import hmac
import urllib.parse

class vnpay:
    def __init__(self):
        self.requestData = {}
        self.responseData = {}

    def get_payment_url(self, base_url, secret_key):
        # Sắp xếp các tham số theo alphabet
        sorted_data = sorted(self.requestData.items())
        query_string = urllib.parse.urlencode(sorted_data)
        
        # Tạo chữ ký (secure hash)
        hmac_obj = hmac.new(secret_key.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha512)
        secure_hash = hmac_obj.hexdigest()
        
        # Ghép URL hoàn chỉnh
        return f"{base_url}?{query_string}&vnp_SecureHash={secure_hash}"

    def validate_response(self, secret_key):
        # Kiểm tra chữ ký từ VNPay trả về có đúng không
        vnp_secure_hash = self.responseData.get('vnp_SecureHash')
        data = self.responseData.copy()
        data.pop('vnp_SecureHash', None)
        data.pop('vnp_SecureHashType', None)
        
        sorted_data = sorted(data.items())
        query_string = urllib.parse.urlencode(sorted_data)
        hmac_obj = hmac.new(secret_key.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha512)
        secure_hash = hmac_obj.hexdigest()
        
        return secure_hash == vnp_secure_hash
