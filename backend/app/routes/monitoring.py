from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.database import get_db
from app.db.models import MonitoringObservation, RegisteredModel, User
from app.routes.auth import oauth2_scheme

router = APIRouter(tags=["monitoring"])


@router.post("/models/{model_id}/monitoring")
def create_observation(model_id: str, payload: dict, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        token_payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.username == token_payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    model = db.query(RegisteredModel).filter(RegisteredModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    obs = MonitoringObservation(
        model_id=model_id,
        total_predictions=int(payload.get("total_predictions", 0)),
        spam_predictions=int(payload.get("spam_predictions", 0)),
        ham_predictions=int(payload.get("ham_predictions", 0)),
        accuracy=float(payload.get("accuracy", 0.0)),
        precision=float(payload.get("precision", 0.0)),
        recall=float(payload.get("recall", 0.0)),
        f1_score=float(payload.get("f1_score", 0.0)),
        health_score=float(payload.get("health_score", 0.0)),
        health_status=str(payload.get("health_status", "UNKNOWN")),
        notes=str(payload.get("notes", "")),
    )
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return {"id": obs.id, "model_id": model_id, "health_status": obs.health_status}


@router.get("/models/{model_id}/monitoring")
def list_observations(model_id: str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    items = db.query(MonitoringObservation).filter(MonitoringObservation.model_id == model_id).all()
    return [{
        "id": item.id,
        "timestamp": item.timestamp.isoformat(),
        "accuracy": item.accuracy,
        "precision": item.precision,
        "recall": item.recall,
        "f1_score": item.f1_score,
        "health_score": item.health_score,
        "health_status": item.health_status,
    } for item in items]
