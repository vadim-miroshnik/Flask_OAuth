"""OAuth endpoints"""

import datetime
from http import HTTPStatus

from flask import abort, jsonify, redirect, request, url_for
from flask_dance.consumer import oauth_authorized
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from flask_dance.contrib.google import google, make_google_blueprint
from flask_login import current_user, login_user
from sqlalchemy.orm.exc import NoResultFound

from api.route.error_messages import ErrMsgEnum
from core.db import db
from core.redis import redis
from core.settings import settings
from models.db_models import OAuth, User
from models.login_history import Login

google_blueprint = make_google_blueprint(
    client_id=settings.oauth.google_client_id,
    client_secret=settings.oauth.google_secret,
#    redirect_to=".after",
    scope=['https://www.googleapis.com/auth/userinfo.email',
           'openid',
           'https://www.googleapis.com/auth/userinfo.profile'],
    authorized_url="/authorized",
    storage=SQLAlchemyStorage(
        OAuth,
        db.session,
        user=current_user,
        user_required=True,
    ),
)

CACHE_EXPIRE_IN_SECONDS = 60 * 60 * 24 * 7


# create/login local user on successful OAuth login
@oauth_authorized.connect_via(google_blueprint)
def google_logged_in(blueprint, token):
    if token:
        resp = google.get("/oauth2/v1/userinfo")
        google_info = resp.json()
        google_user_id = str(google_info["id"])
        email = google_info["email"]
        # Find this OAuth token in the database, or create it
        query = OAuth.query.filter_by(
            provider=blueprint.name,
            provider_user_id=google_user_id,
        )
        try:
            oauth = query.one()
        except NoResultFound:
            user = User.query.filter_by(login=email).first()
            if user:
                abort(HTTPStatus.BAD_REQUEST, description=ErrMsgEnum.LOGIN_EXISTS)
            else:
                oauth = OAuth(
                    provider=blueprint.name,
                    provider_user_id=google_user_id,
                    token=token,
                )
        if not oauth.user:
            user = User.query.filter_by(login=email).first()
            if user:
                abort(HTTPStatus.BAD_REQUEST, description=ErrMsgEnum.LOGIN_EXISTS)
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
        login_user(user)

    return False


@google_blueprint.route("/")
def index():
    if not google.authorized:
        return redirect(url_for("google.login"))
    user = current_user
    access_token = User.encode_auth_token(user.id, None, datetime.timedelta(days=0, minutes=10))
    refresh_token = User.encode_auth_token(user.id, None, datetime.timedelta(days=7))
    ret = {
        "access_token": access_token.decode("utf-8"),
        "refresh_token": refresh_token.decode("utf-8"),
    }
    user_agent = request.headers["User-Agent"]
    user.signin.append(
                Login(
                    login=user.login,
                    dt=datetime.datetime.utcnow(),
                    ip=request.remote_addr,
                    raw_user_agent=user_agent,
                )
            )
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
