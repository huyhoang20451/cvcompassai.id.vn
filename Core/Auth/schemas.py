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
    full_name: Optional[str] = None
    premium_expires: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)

class userinDB(user):
    hashed_password: str

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    Token_type: str

class CandidateCreate(BaseModel):
    username: str | None = None
    password: str
    email: str | None = None
    role: str = "candidate"
    full_name: str | None = None

class BusinessCreate(BaseModel):
    username: str | None = None
    password: str
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