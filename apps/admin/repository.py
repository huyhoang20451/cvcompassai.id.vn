from sqlmodel import Session, func, select
from models import Order_db, User_db, Service_db
from .schemas import OrderSchema, user, Service
from typing import List

# Lấy tất cả các đơn đã thanh toán
def get_paid_orders(session: Session) -> List[OrderSchema]:
    statement = select(Order_db).where(Order_db.status == "paid")
    results = session.exec(statement).all()
    orders = [OrderSchema.model_validate(order_in_db) for order_in_db in results]
    return orders

def get_orders(session: Session) -> List[OrderSchema]:
    statement = select(Order_db)
    results = session.exec(statement).all()
    orders = [OrderSchema.model_validate(order_in_db) for order_in_db in results]
    return orders

# Đếm tổng số đơn hàng
def count_orders(session: Session) -> int:
    statement = select(Order_db)
    results = session.exec(statement).all()
    return len(results)

# Đếm tổng số người dùng
def count_users(session: Session) -> int:
    statement = select(User_db)
    results = session.exec(statement).all()
    return len(results)

# Đếm số người dùng đã mua từng loại gói
def count_users_by_package(session: Session) -> dict:
    statement = (
        select(Order_db.package, func.count(Order_db.user_id))
        .where(Order_db.status == "paid")
        .group_by(Order_db.package)
    )
    results = session.exec(statement).all()
    return dict(results)  # ví dụ: {"candidate_xu": 12, "candidate_premium": 5, ...}

# Tổng tiền thu được cho từng package
def sum_total_money_by_package(session: Session) -> dict:
    statement = (
        select(Order_db.package, func.sum(Order_db.total_money))
        .where(Order_db.status == "paid")
        .group_by(Order_db.package)
    )
    results = session.exec(statement).all()
    # Chuyển None thành 0 nếu package chưa có đơn
    return {pkg: total or 0 for pkg, total in results}

# Tỷ lệ phần trăm đơn hàng bị hủy
def failed_percentage(session: Session) -> float:
    # Đếm tổng số đơn hàng
    total_orders = count_orders(session)
    if total_orders == 0:
        return 0.0
    
    # Đếm số đơn hàng bị hủy
    failed_orders = session.exec(select(func.count(Order_db.id)).where(Order_db.status == "failed")).one()
    return (failed_orders / total_orders) * 100

# Lấy thông tin tất cả user
def get_users(session: Session) -> List[user]:
    statement = select(User_db)
    results = session.exec(statement).all()
    return [user.model_validate(user_in_db) for user_in_db in results]

# Cập nhật thông tin user
def update_user_by_username(
    session: Session, 
    username: str, 
    hashed_password: str | None = None,
    role: str | None = None,
    coin: int | None = None, 
    premium_expires: str | None = None
):
    # Lấy user theo username
    user = session.exec(select(User_db).where(User_db.username == username)).first()
    if not user:
        return None
    user.username = username
    user.hashed_password = hashed_password
    user.role = role
    user.coin = coin
    user.premium_expires = premium_expires

    session.add(user)
    session.commit()
    session.refresh(user)
    return user

# Xoá user theo username
def delete_user_by_username(session: Session, username: str) -> bool:
    # Lấy user theo username
    user = session.exec(select(User_db).where(User_db.username == username)).first()
    if not user:
        return False  # user không tồn tại
    
    session.delete(user)
    session.commit()
    return True

def get_services(session: Session) -> List[Service]:
    results = session.exec(select(Service_db)).all()
    return [Service.model_validate(service_in_db) for service_in_db in results]
