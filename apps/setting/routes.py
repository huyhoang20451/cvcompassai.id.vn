# Chứa API
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Cookie, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from sqlmodel import Session
from .services import upload_avatar
from db import get_session
from Core.Auth.schemas import user
from Core.Auth.dependencies import templates, get_current_user, decode_token, authorize_role
from Core.OCR import run_vintern

router = APIRouter(tags=["setting"])

@router.post("/update_avatar")
async def update_avatar(request: Request,
                        file: UploadFile = File(...),
                        user_info: user = Depends(authorize_role(["candidate", "business"])),
                        session: Session = Depends(get_session)):
    # Kiểm tra loại file
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Chỉ được upload file ảnh")
    avatar_path = await upload_avatar(file, user_info.id, session)
    return templates.TemplateResponse("home_logged_in.html", {"request": request,  # Frontend tự chỉnh return cho hợp lý
                                                              "username": user_info.username}) 
