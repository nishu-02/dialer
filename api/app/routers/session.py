from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..auth import login

router = APIRouter()


class Credentials(BaseModel):
    email: str
    password: str


@router.post("/login")
def do_login(creds: Credentials, request: Request):
    user = login(creds.email, creds.password)
    if not user:
        raise HTTPException(status_code=401, detail="invalid credentials")
    request.session["user_id"] = user["id"]
    return {"id": user["id"], "email": user["email"], "role": user["role"]}


@router.post("/logout")
def do_logout(request: Request):
    request.session.clear()
    return None


@router.get("/me")
def me(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="unauthenticated")
    return {"id": user_id}
