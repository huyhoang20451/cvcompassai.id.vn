from sqlmodel import Session
from .repository import (get_user_by_username as repo_get_user_by_username,
                         save_user_to_db as repo_save_user_to_db,
                         get_user_by_id as repo_get_user_by_id)
from .schemas import userinDB, Login_form, Token
from .hashing import verify_password
from datetime import datetime, timedelta, timezone
from ..config import settings
import jwt
from .hashing import get_password_hash
from .dependencies import get_current_user
from models import User_db

# Lấy thông tin của user bằng username
def get_user_by_username(session: Session, 
                         username: str) -> userinDB:
    user_info = repo_get_user_by_username(session, 
                                          username)
    if not user_info:
        return False
    return userinDB(**user_info.model_dump())

def get_user_by_id(session: Session,
                   user_id: int) -> userinDB:
    user_info = repo_get_user_by_id(session, user_id)
    if not user_info:
        return False
    return userinDB(**user_info.model_dump())

# Verify user
def authenticate_user(session: Session, 
                      username: str,
                      password: str):
    user = get_user_by_username(session, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

# Tạo token
def create_access_token(data: dict, 
                        expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, settings.ALGORITHM)
    return encoded_jwt

# Xác thực và trả token
def login_for_access_token(login_form = Login_form, session = Session) -> Token:
    username = login_form.username
    password = login_form.password
    user = authenticate_user(session, 
                             username,
                             password)
    if not user:
        return False
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub" : user.username, "role": user.role, "company_name": user.company_name},
                                       expires_delta=access_token_expires)
    return Token(access_token=access_token, 
                 Token_type="bearer")

# Đăng ký user
def create_user(session: Session,
                username: str,
                password: str,
                role: str,
                company_name: str):
    user = get_user_by_username(session, username)
    if user:
        return False # Đã có username trong database
    hashed_password = get_password_hash(password)
    new_user = User_db(username=username, hashed_password=hashed_password, role=role, company_name=company_name)
    return repo_save_user_to_db(session, new_user)