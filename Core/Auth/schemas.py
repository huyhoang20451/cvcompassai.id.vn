from pydantic import BaseModel, ConfigDict

class user(BaseModel):
    id: int | None = None
    username: str | None = None
    role: str | None = None
    company_name: str | None = None
    coin: int | None = None
    model_config = ConfigDict(from_attributes=True)
    avatar_path: str | None = None

class userinDB(user):
    hashed_password: str

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    Token_type: str

class UserCreate(BaseModel):
    username: str | None = None
    password: str
    role: str | None = None
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