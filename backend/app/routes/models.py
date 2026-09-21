from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import RegisteredModel, User
from app.routes.auth import oauth2_scheme
from app.core.security import decode_token

router = APIRouter(tags=["models"])


@router.get("/models")
def list_models(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    username = payload.get("sub")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    models = db.query(RegisteredModel).all()
    return [{
        "id": m.id,
        "name": m.name,
        "algorithm": m.algorithm,
        "status": m.status,
        "owner_id": m.owner_id,
    } for m in models]


@router.post("/models")
def create_model(payload: dict, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload_token = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    username = payload_token.get("sub")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    model = RegisteredModel(
        name=payload.get("name"),
        algorithm=payload.get("algorithm", "spam-classifier"),
        status=payload.get("status", "ACTIVE"),
        owner_id=user.id,
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return {"id": model.id, "name": model.name, "status": model.status}
