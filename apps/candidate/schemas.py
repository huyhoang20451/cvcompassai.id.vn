# Chứa các models của dữ liệu giữa các API
from datetime import date, datetime
from pydantic import BaseModel, HttpUrl, ConfigDict
from typing import Optional
class JobSearchRequest(BaseModel):
    keyword: str | None = None
    location: str | None = None

class JobResponse(BaseModel):
    title: str
    description: str
    location: str
    salary: float
    image: HttpUrl

    model_config = ConfigDict(from_attributes=True)

class candidate_CV(BaseModel):
    id: int
    user_id: int
    URL: str

    model_config = ConfigDict(from_attributes=True)

class jd_CV(BaseModel):
    id: int
    jd_id: int
    URL: str

    model_config = ConfigDict(from_attributes=True)

class jd(BaseModel):
    id: Optional[int] = None
    title: str
    salary: str
    location: str
    industry: Optional[str] = None
    position: Optional[str] = None
    company_name: Optional[str] = None
    workplace: Optional[str] = None
    job_description: Optional[str] = None
    requirements: Optional[str] = None
    benefits: Optional[str] = None
    working_time: Optional[str] = None
    application_method: Optional[str] = None
    deadline: Optional[str] = None
    avatar_path: Optional[str] = None

    business_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
