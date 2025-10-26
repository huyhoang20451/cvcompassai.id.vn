from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict

class user(BaseModel):
    id: int | None = None
    username: str | None = None
    role: str | None = None
    company_name: str | None = None
    coin: int | None = None
    avatar_path: str | None = None
    premium_expires: Optional[date] = None
    email: Optional[str] = None
    
    # Các trường chỉ dành cho candidate
    full_name: Optional[str] = None

    # Các trường chỉ dành cho business
    company_name: Optional[str] = None
    company_description: Optional[str] = None
    website: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class userinDB(user):
    hashed_password: str

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    Token_type: str

class CandidateCreate(BaseModel):
    username: str | None = None
    password: str | None = None
    email: str | None = None
    role: str = "candidate"
    full_name: str | None = None

class BusinessCreate(BaseModel):
    username: str | None = None
    password: str | None = None
    email: str | None = None
    role: str = "business"
    company_name: str | None = None

class Login_form(BaseModel):
    username: str | None = None
    password: str

class jd(BaseModel):
    id: int
    company_logo: str
    job_title: str
    company_name: str
    salary: str
    location: str
    details: dict