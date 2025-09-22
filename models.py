# Chứa các models của database
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone, date
from apps.business.schemas import JD_form
import json

class User_db(SQLModel, table=True):
    __tablename__ = "user"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(nullable=False, max_length=100, unique=True)
    hashed_password: str = Field(nullable=False, max_length=255)
    role: str = Field(nullable=False, max_length=50)  # "candidate" hoặc "business"
    avatar_path: Optional[str] = Field(default=None, max_length=255)
    coin: Optional[int] = Field(default=0)

    # Các trường chỉ dành cho business
    company_name: Optional[str] = Field(default=None, max_length=100)
    location: Optional[str] = Field(default=None, max_length=100)

class jd_db(SQLModel, table=True):
    __tablename__ = "jd"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(nullable=False, max_length=100)
    location: str = Field(nullable=False, max_length=1000)
    salary: Optional[str] = Field(default=None, max_length=50)
    industry: Optional[str] = Field(default=None, max_length=255)
    position: Optional[str] = Field(default=None, max_length=255)
    company: Optional[str] = Field(default=None, max_length=255)
    workplace: Optional[str] = Field(default=None, max_length=255)
    job_description: Optional[str] = Field(default=None)
    requirements: Optional[str] = Field(default=None)
    benefits: Optional[str] = Field(default=None)
    working_time: Optional[str] = Field(default=None, max_length=255)
    application_method: Optional[str] = Field(default=None, max_length=255)
    deadline: Optional[str] = Field(default=None, max_length=255)
    business_id: Optional[int] = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(nullable=True)
    
class candidate_CV_db(SQLModel, table=True):
    __tablename__ = "candidate_CV"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")   # liên kết với bảng users
    URL: str = Field(max_length=255)

class jd_CV_db(SQLModel, table=True):
    __tablename__ = "jd_CV"

    id: Optional[int] = Field(default=None, primary_key=True)
    jd_id: int = Field(foreign_key="jd.id")   # liên kết với bảng job
    URL: str = Field(max_length=255)