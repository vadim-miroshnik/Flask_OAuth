"""Login history db model"""

import uuid

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from core.db import db


class Login(db.Model):
    __tablename__ = "history"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    dt = db.Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    login = db.Column(db.String, nullable=False)
    ip = db.Column(db.String, nullable=False)
    user_agent = db.Column(db.String, nullable=False)
