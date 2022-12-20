"""Login history db model"""
import uuid

from sqlalchemy import DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func
from user_agents import parse

from core.db import db


def create_partition(target, connection, **kw) -> None:
    """creating partition by user_sign_in"""
    connection.execute(
        """CREATE TABLE IF NOT EXISTS "user_sign_in_other" PARTITION OF "history" FOR VALUES IN ('other')"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS "user_sign_in_mobile" PARTITION OF "history" FOR VALUES IN ('mobile')"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS "user_sign_in_web" PARTITION OF "history" FOR VALUES IN ('web')"""
    )


class Login(db.Model):
    __tablename__ = "history"
    __table_args__ = (
        UniqueConstraint('id', 'user_device_type'),
        {
            'postgresql_partition_by': 'LIST (user_device_type)',
            'listeners': [('after_create', create_partition)],
        }
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"))
    dt = db.Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    login = db.Column(db.String, nullable=False)
    ip = db.Column(db.String, nullable=False)
    user_agent = db.Column(db.String, nullable=False)
    user_device_type = db.Column(db.Text, primary_key=True)

    @hybrid_property
    def raw_user_agent(self):
        return self.user_device_type

    @raw_user_agent.setter
    def raw_user_agent(self, plaintext):
        self.user_agent = plaintext
        try:
            user_agent = parse(plaintext)
            if user_agent.is_mobile:
                self.user_device_type = "mobile"
            elif user_agent.is_pc:
                self.user_device_type = "web"
            else:
                self.user_device_type = "other"
        except KeyError:
            self.user_device_type = "error"

    def __repr__(self):
        return f"<UserSignIn {self.user_id}:{self.logged_in_at }>"

