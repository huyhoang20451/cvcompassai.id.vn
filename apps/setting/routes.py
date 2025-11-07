# Chứa API
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Cookie, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from sqlmodel import Session
from .services import (upload_avatar, 
                       update_user as service_update_user)
from db import get_session
from Core.Auth.schemas import user
from Core.Auth.dependencies import templates, authorize_role

router = APIRouter(tags=["setting"])

@router.get("/load-avatar")
async def load_avatar(user_info: user = Depends(authorize_role(["candidate"]))):
    # Trả về đường dẫn ảnh avatar dạng JSON
    return {"avatar_path": user_info.avatar_path}

@router.post("/update_avatar")
async def update_avatar(request: Request,
                        file: UploadFile = File(...),
                        user_info: user = Depends(authorize_role(["candidate", "business"])),
                        session: Session = Depends(get_session)):
    # Kiểm tra loại file
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Chỉ được upload file ảnh")
    avatar_path = await upload_avatar(file, user_info.id, session)
    return templates.TemplateResponse("home_logged_in.html", {"request": request, # Frontend tự chỉnh return cho hợp lý
                                                              "user_avatar": avatar_path,
                                                              "username": user_info.username})
    # return JSONResponse(content={"avatar_path": avatar_path})

@router.post("/edit-profile")
async def update_user(request: Request,
                      user_info: user = Depends(authorize_role(["candidate", "business"])),
                      session: Session = Depends(get_session)):
    # Lấy toàn bộ dữ liệu form
    form = await request.form()
    update_data = dict(form)
    
    if not update_data:
        raise HTTPException(status_code=400, detail="Không có dữ liệu form để cập nhật")
    
    try:
        update_result = service_update_user(session, user_info.id, update_data)
        if update_result:
            return JSONResponse(content={"message": "Cập nhật thông tin user thành công"})
        else:
            raise HTTPException(status_code=500, detail="Cập nhật thông tin user thất bại")
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))