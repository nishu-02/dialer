from fastapi import HTTPException, Request
from passlib.hash import bcrypt

from .db import get_conn


def require_auth(request: Request) -> int:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="unauthenticated")
    return user_id


def login(email: str, password: str):
    conn = get_conn()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    if not user or not bcrypt.verify(password, user["pass_hash"]):
        return None
    return user


def create_user(email: str, password: str, role: str = "rep"):
    conn = get_conn()
    conn.execute(
        "INSERT INTO users (email, pass_hash, role) VALUES (?, ?, ?)",
        (email, bcrypt.hash(password), role),
    )
    conn.commit()
    conn.close()
