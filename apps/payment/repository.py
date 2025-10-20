# Truy vấn cơ sỏ dữ liệu
from datetime import date
from sqlmodel import Session, select
from models import Order_db, User_db, Service_db
from .schemas import OrderSchema, packageInfo
from sqlalchemy import or_
from typing import List, Optional
from apps.candidate.repository import update_coin as repo_update_coin

def create_order(order: OrderSchema, session: Session) -> OrderSchema:
    """Tạo Order mới (insert), chưa hỗ trợ update"""
    order_db = Order_db(**order.model_dump())
    session.add(order_db)
    session.commit()
    session.refresh(order_db)  # đảm bảo lấy dữ liệu mới nhất từ DB

    return OrderSchema.model_validate(order_db)

def get_order(id: str, session: Session) -> OrderSchema:
    statement = select(Order_db).where(Order_db.id == id)
    order = session.exec(statement).first()
    return OrderSchema.model_validate(order)

def update_user_role(id: int, new_role: str, session: Session):
    statement = select(User_db).where(User_db.id == id)
    user = session.exec(statement).first()
    if user:
        user.role = new_role
        session.add(user)
        session.commit()
        session.refresh(user)
    return user

def update_user_expires_premium(id: int, new_expires: date, session: Session):
    statement = select(User_db).where(User_db.id == id)
    user = session.exec(statement).first()
    if user:
        user.premium_expires = new_expires
        session.add(user)
        session.commit()
        session.refresh(user)
    return user

def update_order_status(id: str, new_status: str, session: Session) -> OrderSchema:
    statement = select(Order_db).where(Order_db.id == id)
    order = session.exec(statement).first()
    if order:
        order.status = new_status
        session.add(order)
        session.commit()
        session.refresh(order)
    return OrderSchema.model_validate(order)

def get_package_info_by_name(package_name: str, session: Session):
    statement = select(Service_db).where(Service_db.name == package_name)
    package = session.exec(statement).first()
    return packageInfo.model_validate(package)

def get_packages(session: Session) -> List[packageInfo]:
    statement = select(Service_db)
    packages = session.exec(statement).all()
    return [packageInfo.model_validate(pkg) for pkg in packages]