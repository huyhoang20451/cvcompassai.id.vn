from datetime import date, datetime
from pydantic import BaseModel, HttpUrl, ConfigDict, EmailStr
from typing import List, Optional

# Thông tin jd lúc tạo
class JD_create(BaseModel):
    id: Optional[int] = None
    title: str
    location: Optional[str] = None
    min_salary: Optional[int] = None
    max_salary: Optional[int] = None
    business_id: Optional[int] = None
    created_at: datetime
    job_category: Optional[str] = None
    position: Optional[str] = None
    job_description: Optional[str] = None
    requirements: Optional[str] = None
    benefits: Optional[str] = None
    working_time: Optional[str] = None
    application_method: Optional[str] = None
    deadline: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# Thông tin jd lúc trả về (có thêm tên công ty và avatar)
class jd_response(JD_create):
    company_name: Optional[str] = None
    avatar_path: Optional[str] = None
    cv_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)
    
class OCR_result(BaseModel):
    Met: List[str]
    Not_Met: List[str]
    Met_Count: int
    Not_Met_Count: int
    Total: int
    Ratio: float
    Ratio_Percent: float

class candidate_CV(BaseModel):
    id: int
    user_id: int
    URL: str

    model_config = ConfigDict(from_attributes=True)

class jd_CV(BaseModel):
    id: int
    jd_id: int
    URL: str
    candidate_id: int
    
    model_config = ConfigDict(from_attributes=True)

class JobCategory(BaseModel):
    id: int
    job_category: str

    model_config = ConfigDict(from_attributes=True)

class EmailRequest(BaseModel):
    to: EmailStr
    subject: str
    content: str