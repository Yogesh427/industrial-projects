from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.database import get_db
from app.db.models import DecisionLog, MonitoringObservation, RegisteredModel, User
from app.routes.auth import oauth2_scheme

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def dashboard(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    models = db.query(RegisteredModel).all()
    summary = []
    for model in models:
        observations = db.query(MonitoringObservation).filter(MonitoringObservation.model_id == model.id).all()
        decisions = db.query(DecisionLog).filter(DecisionLog.model_id == model.id).all()
        latest_observation = observations[-1] if observations else None
        summary.append({
            "id": model.id,
            "model": model.name,
            "algorithm": model.algorithm,
            "status": model.status,
            "observations": len(observations),
            "recommendations": len(decisions),
            "latest_health": latest_observation.health_status if latest_observation else "UNKNOWN",
            "latest_health_score": latest_observation.health_score if latest_observation else 0,
        })
    return {"models": summary}
