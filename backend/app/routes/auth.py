from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import create_access_token, decode_token, hash_password, verify_password
from app.db.database import get_db
from app.db.models import User

router = APIRouter(tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")


@router.post("/register")
def register_user(payload: dict, db: Session = Depends(get_db)):
    email = payload.get("email")
    username = payload.get("username")
    password = payload.get("password")
    role = payload.get("role", "VIEWER")

    if not email or not username or not password:
        raise HTTPException(status_code=400, detail="Email, username, and password are required")

    existing = db.query(User).filter((User.email == email) | (User.username == username)).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(
        email=email,
        username=username,
        hashed_password=hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "username": user.username, "role": user.role}


@router.post("/login")
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(user.username)
    return {"access_token": token, "token_type": "bearer", "user": {"id": user.id, "username": user.username, "role": user.role}}


@router.get("/me")
def get_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    username = payload.get("sub")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "email": user.email, "username": user.username, "role": user.role}
