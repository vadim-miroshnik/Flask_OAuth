"""DB modeles"""

import base64
import datetime
import enum
import json
import secrets
import string
import uuid

import jwt
from pbkdf2 import crypt
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func

from core.db import db
from core.settings import settings
from models.uuid_encoder import UUIDEncoder


association_user_roles = db.Table(
    "association_user_roles",
    db.Model.metadata,
    db.Column("users_id", db.ForeignKey("users.id")),
    db.Column("roles_id", db.ForeignKey("roles.id")),
)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    login = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    roles = db.relationship("Role", secondary=association_user_roles)
    signin = db.relationship("Login", cascade="all,delete")

    @hybrid_property
    def plain_password(self):
        return self.password

    @plain_password.setter
    def plain_password(self, plaintext):
        alphabet = string.ascii_letters + string.digits
        salt = "".join(secrets.choice(alphabet) for _ in range(settings.app.salt_length))
        hpswd = crypt(plaintext, salt, iterations=settings.app.psw_hash_iterations)
        parts_hpswd = hpswd.split("$")
        self.password = f"{parts_hpswd[3]}{parts_hpswd[4]}"

    def check_password(self, plaintext):
        salt = self.password[: settings.app.salt_length]
        hpswd = crypt(plaintext, salt, iterations=settings.app.psw_hash_iterations)
        hpswd_db = "$".join(
            [
                "",
                settings.app.kdf_algorithm,
                f"{settings.app.psw_hash_iterations:x}",
                salt,
                self.password[settings.app.salt_length :],
            ]
        )
        return hpswd == hpswd_db

    @staticmethod
    def encode_auth_token(user_id, role, exp):
        try:
            payload = {
                "exp": datetime.datetime.utcnow() + exp,
                "iat": datetime.datetime.utcnow(),
                "nbf": datetime.datetime.utcnow(),
                "sub": json.dumps(user_id, cls=UUIDEncoder),
                "role": role if role else "user",
            }
            return jwt.encode(
                payload,
                key=base64.b64decode(settings.app.jwt_secret_key),
                algorithm="HS256",
            )
        except Exception as e:
            return e


class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    users = db.relationship("User", secondary=association_user_roles)
    name = db.Column(db.String, nullable=False, unique=True)
    permissions = db.relationship("Permission", cascade="all,delete")


class PermissionType(enum.Enum):
    all_read = "All read"
    all_write = "All write"


class Permission(db.Model):
    __tablename__ = "permissions"
    name = db.Column(db.Enum(PermissionType), primary_key=True, nullable=False)
    id_role = db.Column(UUID(as_uuid=True), db.ForeignKey("roles.id"))


class Token(db.Model):
    id = db.Column(db.String, nullable=False, primary_key=True)
    time_created = db.Column(db.DateTime, server_default=func.now())
    expired_time = db.Column(db.DateTime)
