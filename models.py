# Chứa các models của database
import uuid
from sqlalchemy import Column, DateTime, func
from sqlmodel import SQLModel, Field, UniqueConstraint
from typing import Optional, Text
from datetime import datetime, timezone, date
import json
from apps.payment.schemas import OrderStatus
class User_db(SQLModel, table=True):
    __tablename__ = "user"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(nullable=False, max_length=100, unique=True)
    hashed_password: str = Field(nullable=False, max_length=255)
    email: Optional[str] = Field(default=None, max_length=100, unique=True)
    role: str = Field(nullable=False, max_length=50)  # "candidate" hoặc "business"
    avatar_path: Optional[str] = Field(default=None, max_length=255)
    coin: Optional[int] = Field(default=0)
    premium_expires: Optional[date] = Field(default=None)

    # Các trường chỉ dành cho candidate
    full_name: Optional[str] = Field(default=None, max_length=100)

    # Các trường chỉ dành cho business
    company_name: Optional[str] = Field(default=None, max_length=100)
    company_description: Optional[str] = Field(default=None)  # TEXT trong MySQL
    website: Optional[str] = Field(default=None, max_length=255)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    address: Optional[str] = Field(default=None, max_length=255)

class jd_db(SQLModel, table=True):
    __tablename__ = "jd"  # Tên bảng trong database: lưu thông tin các job posting (tin tuyển dụng)

    id: Optional[int] = Field(default=None, primary_key=True) # ID duy nhất của mỗi tin tuyển dụng (primary key, auto-increment)
    title: str = Field(nullable=False, max_length=100) # Tiêu đề tin tuyển dụng, ví dụ: "Lập trình viên Python", "Chuyên viên Marketing"
    location: str = Field(nullable=False, max_length=1000) # Địa điểm làm việc, có thể bao gồm nhiều nơi hoặc mô tả chi tiết như "Hà Nội / Remote"
    min_salary: Optional[int] = Field(default=None, description="Mức lương tối thiểu (đơn vị: VNĐ)")
    max_salary: Optional[int] = Field(default=None, description="Mức lương tối đa (đơn vị: VNĐ)")
    business_id: Optional[int] = Field(default=None, foreign_key="user.id") # Khóa ngoại liên kết đến bảng `user` — xác định người/tài khoản doanh nghiệp nào đăng tin
    created_at: datetime = Field(nullable=True) # Ngày tạo tin (thường set mặc định = thời điểm đăng tuyển)
    job_category: Optional[str] = Field(default=None, max_length=255) # Ngành nghề hoặc lĩnh vực (ví dụ: "Công nghệ thông tin", "Thiết kế", "Kế toán")
    position: Optional[str] = Field(default=None, max_length=255) # Vị trí cụ thể trong công ty, ví dụ: "Trưởng nhóm", "Nhân viên", "Thực tập sinh"
    job_description: Optional[str] = Field(default=None) # Mô tả công việc chi tiết – các nhiệm vụ, trách nhiệm chính của vị trí
    requirements: Optional[str] = Field(default=None) # Yêu cầu ứng viên: kỹ năng, kinh nghiệm, trình độ học vấn...
    benefits: Optional[str] = Field(default=None) # Quyền lợi được hưởng: lương thưởng, chế độ nghỉ, bảo hiểm, phúc lợi...
    working_time: Optional[str] = Field(default=None, max_length=255) # Thời gian làm việc: "T2–T6", "Ca xoay", "Giờ hành chính"...
    application_method: Optional[str] = Field(default=None, max_length=255) # Cách thức ứng tuyển: "Gửi CV qua email", "Ứng tuyển trên web", "Liên hệ trực tiếp"
    deadline: Optional[str] = Field(default=None, max_length=255) # Hạn chót nộp hồ sơ (deadline tuyển dụng)
    
class candidate_CV_db(SQLModel, table=True):
    __tablename__ = "candidate_CV"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")   # liên kết với bảng users
    URL: str = Field(max_length=255)
    details: Optional[str] = Field(default=None, max_length=2000)  # đổi sang VARCHAR(2000)

class jd_CV_db(SQLModel, table=True):
    __tablename__ = "jd_CV"

    id: Optional[int] = Field(default=None, primary_key=True)
    jd_id: int = Field(foreign_key="jd.id")   # liên kết với bảng job
    URL: str = Field(max_length=255)

class Order_db(SQLModel, table=True):
    __tablename__ = "orders"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, index=True)
    user_id: int = Field(foreign_key="user.id")
    package: str
    amount: int
    total_money: int
    description: Optional[str] = None
    status: OrderStatus = Field(default=OrderStatus.pending)
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),   # chỉ set khi insert
            nullable=False
        )
    )

class Service_db(SQLModel, table=True):
    __tablename__ = "services"

    id: int = Field(default=None, primary_key=True)  # autoincrement mặc định với int PK
    name: str = Field(nullable=False, max_length=100, unique=True)
    description: Optional[str] = Field(default=None, max_length=255)
    price: int = Field(nullable=False)

class SavedJob(SQLModel, table=True):
    __tablename__ = "saved_jobs"
    __table_args__ = (UniqueConstraint("candidate_id", "job_id", name="unique_saved_job"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_id: int = Field(foreign_key="user.id", nullable=False)
    job_id: int = Field(foreign_key="jd.id", nullable=False)
    saved_at: datetime = Field(default_factory=datetime.utcnow)

class JobCategory_db(SQLModel, table=True):
    __tablename__ = "job_category"

    id: int = Field(default=None, primary_key=True)  # Tự động tăng (autoincrement)
    job_category: str = Field(nullable=False, max_length=100, unique=True)

class Package_db(SQLModel, table=True):
    __tablename__ = "package"

    id: int = Field(default=None, primary_key=True)
    name_package: str = Field(nullable=False, max_length=100, unique=True)
    price: float = Field(nullable=False)  # hoặc Decimal nếu muốn chính xác hơn