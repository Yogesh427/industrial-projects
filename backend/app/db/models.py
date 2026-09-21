import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="VIEWER", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    models = relationship("RegisteredModel", back_populates="owner")


class RegisteredModel(Base):
    __tablename__ = "registered_models"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    algorithm = Column(String, default="spam-classifier")
    status = Column(String, default="ACTIVE")
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="models")
    observations = relationship("MonitoringObservation", back_populates="model")
    decisions = relationship("DecisionLog", back_populates="model")


class MonitoringObservation(Base):
    __tablename__ = "monitoring_observations"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    model_id = Column(String, ForeignKey("registered_models.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    total_predictions = Column(Integer, default=0)
    spam_predictions = Column(Integer, default=0)
    ham_predictions = Column(Integer, default=0)
    accuracy = Column(Float, default=0.0)
    precision = Column(Float, default=0.0)
    recall = Column(Float, default=0.0)
    f1_score = Column(Float, default=0.0)
    health_score = Column(Float, default=0.0)
    health_status = Column(String, default="UNKNOWN")
    notes = Column(Text, default="")

    model = relationship("RegisteredModel", back_populates="observations")


class DecisionLog(Base):
    __tablename__ = "decision_logs"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    model_id = Column(String, ForeignKey("registered_models.id"), nullable=False)
    health_score = Column(Float, default=0.0)
    health_status = Column(String, default="UNKNOWN")
    recommended_action = Column(String, default="CONTINUE_MONITORING")
    priority = Column(String, default="MEDIUM")
    rationale = Column(Text, default="")
    requires_human_approval = Column(Boolean, default=True)
    approval_status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)

    model = relationship("RegisteredModel", back_populates="decisions")
