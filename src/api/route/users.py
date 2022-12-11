"""Users endpoints"""

import datetime
import logging
from http import HTTPStatus

from flasgger import swag_from
from flask import Blueprint, abort, jsonify, request
from flask_dance.consumer import OAuth2ConsumerBlueprint, oauth_authorized
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from flask_dance.contrib.google import google, make_google_blueprint
from flask_jwt import current_identity, jwt_required
from flask_login import current_user
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy_paginator import Paginator

from api.route.error_messages import ErrMsgEnum
from api.schema.login import LoginSchema, LoginsSchema
from api.schema.signin import SignInSchema
from api.schema.user import UserSchema
from core.db import db
from core.redis import redis
from core.settings import settings
from models.db_models import OAuth, User
from models.login_history import Login

users_api = Blueprint("users", __name__)

google_blueprint = make_google_blueprint(
    client_id=settings.oauth.google_client_id,
    client_secret=settings.oauth.google_secret,
    scope=['https://www.googleapis.com/auth/userinfo.email',
           'openid',
           'https://www.googleapis.com/auth/userinfo.profile'],
    storage=SQLAlchemyStorage(
        OAuth,
        db.session,
        user=current_user,
        user_required=False,
    ),
)

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

# create/login local user on successful OAuth login
@oauth_authorized.connect_via(google_blueprint)
def google_logged_in(blueprint, token):
    if google.authorized:
        resp = google.get("/oauth2/v1/userinfo")
        google_info = resp.json()
        google_user_id = str(google_info["id"])

        # Find this OAuth token in the database, or create it
        query = OAuth.query.filter_by(
            provider=blueprint.name,
            provider_user_id=google_user_id,
        )
        try:
            oauth = query.one()
        except NoResultFound:
            oauth = OAuth(
                provider=blueprint.name,
                provider_user_id=google_user_id,
                token=token,
            )
        email = google_info["email"]
        if oauth.user:
            # If this OAuth token already has an associated local account,
            # log in that local user account.
            # Note that if we just created this OAuth token, then it can't
            # have an associated local account yet.
            user = User.query.filter_by(login=email).first()

        else:
            # If this OAuth token doesn't have an associated local account,
            # create a new local user account for this user. We can log
            # in that account as well, while we're at it.
            new_user = User(
                # Remember that `email` can be None, if the user declines
                # to publish their email address on Google!
                login=email,
                plain_password="",
            )
            # Associate the new local user account with the OAuth token
            oauth.user = new_user
            # Save and commit our database models
            db.session.add_all([new_user, oauth])
            db.session.commit()
            # Log in the new local user account
            user = User.query.filter_by(login=email).first()
            access_token = User.encode_auth_token(user.id, None, datetime.timedelta(days=0, minutes=10))
            refresh_token = User.encode_auth_token(user.id, None, datetime.timedelta(days=7))
            ret = {
                "access_token": access_token.decode("utf-8"),
                "refresh_token": refresh_token.decode("utf-8"),
            }

            user_agent = request.headers["User-Agent"]

            login_user = Login(
                login=email,
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

        # Since we're manually creating the OAuth model in the database,
        # we should return False so that Flask-Dance knows that
        # it doesn't have to do it. If we don't return False, the OAuth token
        # could be saved twice, or Flask-Dance could throw an error when
        # trying to incorrectly save it for us.
        return False
