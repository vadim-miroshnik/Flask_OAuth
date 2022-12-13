"""Users endpoints"""

import datetime
import logging
from http import HTTPStatus

from flasgger import swag_from
from flask import Blueprint, abort, jsonify, request
from flask_jwt import current_identity, jwt_required
from sqlalchemy_paginator import Paginator

from api.route.error_messages import ErrMsgEnum
from api.schema.login import LoginSchema, LoginsSchema
from api.schema.signin import SignInSchema
from api.schema.user import UserSchema
from core.db import db
from core.redis import redis
from models.db_models import User
from models.login_history import Login

users_api = Blueprint("users", __name__)

CACHE_EXPIRE_IN_SECONDS = 60 * 60 * 24 * 7
PAGE_SIZE = 10


@users_api.route("/register", methods=["POST"])
@swag_from(
    {
        "tags": ["users"],
        "parameters": [{"in": "body", "name": "body", "required": "true", "schema": UserSchema}],
        "responses": {
            int(HTTPStatus.CREATED): {
                "description": "Register",
                "schema": {"type": "string"},
            },
            int(HTTPStatus.BAD_REQUEST): {
                "description": "Bad request",
                "schema": {"type": "string"},
            },
        },
    }
)
def register():
    content_type = request.headers.get("Content-Type")
    if content_type == "application/json":
        login = request.json["login"]
        user = User.query.filter_by(login=login).first()
        if user and login == user.login:
            abort(HTTPStatus.BAD_REQUEST, description=ErrMsgEnum.LOGIN_EXISTS)
        password = request.json["password"]
        if len(password) < 6:
            abort(HTTPStatus.BAD_REQUEST, description=ErrMsgEnum.PASSWORD_ERROR)
        user = User(login=login, plain_password=password)
        db.session.add(user)
        db.session.commit()
        new_user = User.query.filter_by(login=login).first()
        access_token = User.encode_auth_token(new_user.id, None, datetime.timedelta(days=0, minutes=10))
        refresh_token = User.encode_auth_token(new_user.id, None, datetime.timedelta(days=7))
        ret = {
            "access_token": access_token.decode("utf-8"),
            "refresh_token": refresh_token.decode("utf-8"),
        }

        user_agent = request.headers["User-Agent"]

        login_user = Login(
            login=login,
            dt=datetime.datetime.utcnow(),
            ip=request.remote_addr,
            user_agent=user_agent,
        )
        db.session.add(login_user)
        db.session.commit()

        redis.set(
            f"refresh_token:{new_user.id}:{user_agent}",
            refresh_token.decode("utf-8"),
            ex=CACHE_EXPIRE_IN_SECONDS,
        )

        redis.set(
            refresh_token.decode("utf-8"),
            f"{new_user.id}::{new_user.roles}",
            ex=CACHE_EXPIRE_IN_SECONDS,
        )

        return jsonify(ret), HTTPStatus.CREATED
    abort(HTTPStatus.BAD_REQUEST, description=ErrMsgEnum.CONTENT_NOT_SUPPORTED)


@users_api.route("/login", methods=["POST"])
@swag_from(
    {
        "tags": ["users"],
        "parameters": [{"in": "body", "name": "body", "required": "true", "schema": SignInSchema}],
        "responses": {
            int(HTTPStatus.CREATED): {
                "description": "Login",
                "schema": {"type": "string"},
            },
            int(HTTPStatus.BAD_REQUEST): {
                "description": "Bad request",
                "schema": {"type": "string"},
            },
        },
    }
)
def login():
    content_type = request.headers.get("Content-Type")
    if content_type == "application/json":
        login = request.json["login"]
        password = request.json["password"]
        if not login and not password:
            abort(HTTPStatus.BAD_REQUEST, description=ErrMsgEnum.INPUT_ERROR)
        if not (user := User.query.filter_by(login=login).first()):
            abort(HTTPStatus.BAD_REQUEST, description=ErrMsgEnum.LOGIN_NOT_EXISTS)
        else:
            if user.check_password(password):
                role = ",".join([role.name for role in user.roles])
                access_token = User.encode_auth_token(user.id, role, datetime.timedelta(days=0, minutes=10))
                refresh_token = User.encode_auth_token(user.id, role, datetime.timedelta(days=7))
                ret = {
                    "access_token": access_token.decode("utf-8"),
                    "refresh_token": refresh_token.decode("utf-8"),
                }

                user_agent = request.headers["User-Agent"]

                login_user = Login(
                    login=login,
                    dt=datetime.datetime.utcnow(),
                    ip=request.remote_addr,
                    user_agent=user_agent,
                )
                db.session.add(login_user)
                db.session.commit()

                redis.set(
                    f"refresh_token:{user.id}:{user_agent}",
                    refresh_token.decode("utf-8"),
                    ex=CACHE_EXPIRE_IN_SECONDS,
                )

                redis.set(
                    refresh_token.decode("utf-8"),
                    f"{user.id}::{user.roles}",
                    ex=CACHE_EXPIRE_IN_SECONDS,
                )

                return jsonify(ret), HTTPStatus.CREATED
            else:
                abort(HTTPStatus.BAD_REQUEST, description=ErrMsgEnum.PASSWORD_NOT_MATCH)
    abort(HTTPStatus.BAD_REQUEST, description=ErrMsgEnum.CONTENT_NOT_SUPPORTED)


@users_api.route("/logout", methods=["POST"])
@swag_from(
    {
        "tags": ["users"],
        "parameters": [
            {
                "in": "header",
                "name": "Authorization",
                "required": "true",
                "description": "JWT token",
                "schema": {"type": "string"},
            }
        ],
        "responses": {
            int(HTTPStatus.CREATED): {
                "description": "Logout",
                "schema": {"type": "string"},
            },
            int(HTTPStatus.UNAUTHORIZED): {
                "description": "Unauthorized",
                "schema": {"type": "string"},
            },
        },
    }
)
@jwt_required()
def logout():
    key = f"refresh_token:{current_identity.id}:{request.headers['User-Agent']}"
    refresh_token = redis.get(key)
    redis.delete(key)
    redis.delete(refresh_token)
    return jsonify(dict(status="success")), HTTPStatus.CREATED


@users_api.route("/logout-all", methods=["POST"])
@swag_from(
    {
        "tags": ["users"],
        "parameters": [
            {
                "in": "header",
                "name": "Authorization",
                "required": "true",
                "description": "JWT token",
                "schema": {"type": "string"},
            }
        ],
        "responses": {
            HTTPStatus.CREATED.value: {
                "description": "Logout",
                "schema": {"type": "string"},
            },
            HTTPStatus.UNAUTHORIZED.value: {
                "description": "Unauthorized",
                "schema": {"type": "string"},
            },
        },
    }
)
@jwt_required()
def logout_all():
    logins = Login.query.filter_by(login=current_identity.login).all()
    used = set()
    unique_agents = [
        login.user_agent for login in logins if login.user_agent not in used and (used.add(login.user_agent) or True)
    ]
    for agent in unique_agents:
        key = f"refresh_token:{current_identity.id}:{agent}"
        refresh_token = redis.get(key)
        redis.delete(key)
        redis.delete(refresh_token)
    return jsonify(dict(status="success")), HTTPStatus.CREATED


@users_api.route("/profile", methods=["PUT"])
@swag_from(
    {
        "tags": ["users"],
        "parameters": [
            {
                "in": "header",
                "name": "Authorization",
                "required": "true",
                "description": "JWT token",
                "schema": {"type": "string"},
            },
            {"in": "body", "name": "body", "required": "true", "schema": UserSchema},
        ],
        "responses": {
            int(HTTPStatus.CREATED): {
                "description": "Update profile",
                "schema": UserSchema,
            },
            int(HTTPStatus.BAD_REQUEST): {
                "description": "Bad request",
                "schema": {"type": "string"},
            },
            int(HTTPStatus.UNAUTHORIZED): {
                "description": "Unauthorized",
                "schema": {"type": "string"},
            },
        },
    }
)
@jwt_required()
def update_user():
    content_type = request.headers.get("Content-Type")
    if content_type == "application/json":
        password = request.json["password"]
        if len(password) < 6:
            abort(HTTPStatus.BAD_REQUEST, description=ErrMsgEnum.PASSWORD_ERROR)
        current_identity.plain_password = password
        db.session.commit()
        return UserSchema().dump(current_identity), HTTPStatus.CREATED
    abort(HTTPStatus.BAD_REQUEST, description=ErrMsgEnum.CONTENT_NOT_SUPPORTED)


@users_api.route("/history/<int:page>", methods=["GET"])
@swag_from(
    {
        "tags": ["users"],
        "parameters": [
            {
                "in": "header",
                "name": "Authorization",
                "required": "true",
                "description": "JWT token",
                "schema": {"type": "string"},
            },
            {"in": "path", "name": "page", "schema": {"type": "int"}}
        ],
        "responses": {
            int(HTTPStatus.OK): {
                "description": "Login history",
                "schema": LoginsSchema,
            },
            int(HTTPStatus.UNAUTHORIZED): {
                "description": "Unauthorized",
                "schema": {"type": "string"},
            },
        },
    }
)
@jwt_required()
def login_history(page: int):
    query = Login.query.filter_by(login=current_identity.login)
    paginator = Paginator(query, PAGE_SIZE)
    page = paginator.page(page)
    return LoginsSchema().dump(dict(logins=page.object_list)), HTTPStatus.OK


@users_api.route("/refresh", methods=["POST"])
@swag_from(
    {
        "tags": ["users"],
        "parameters": [
            {
                "in": "body",
                "name": "refresh-token",
                "required": "true",
                "description": "JWT refresh_token",
                "schema": {"type": "string"},
            },
        ],
        "responses": {
            int(HTTPStatus.OK): {
                "description": "Refresh",
                "schema": {"type": "string"},
            },
            int(HTTPStatus.BAD_REQUEST): {
                "description": "Bad request",
                "schema": {"type": "string"},
            },
        },
    }
)
def refresh():
    user = redis.get(request.data.decode("utf-8"))
    if user:
        user_parts = user.decode("utf-8").split("::")
        access_token = User.encode_auth_token(
            user_parts[0],
            user_parts[1],
            datetime.timedelta(days=0, minutes=10),
        )
        return jsonify(dict(access_token=access_token.decode("utf-8"))), HTTPStatus.OK
    else:
        abort(HTTPStatus.BAD_REQUEST, description=ErrMsgEnum.NO_REFRESH_TOKEN)

