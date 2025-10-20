
from payos import PayOS
from Core.config import settings

client_id = settings.PAYOS_CLIENT_ID
api_key = settings.PAYOS_API_KEY
checksum_key = settings.PAYOS_CHECKSUM_KEY

payOS = PayOS(client_id=client_id, api_key=api_key, checksum_key=checksum_key)