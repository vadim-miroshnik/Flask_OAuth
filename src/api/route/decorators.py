"""Auth decorators"""

import logging
from functools import wraps
from http import HTTPStatus

from flask_jwt import current_identity
from flask import abort

from rate_limiter.limiter import DurationEnum
from rate_limiter.limiter import Limiter
from rate_limiter.request_rate import RequestRate
from rate_limiter.redis_bucket import RedisBucket

from models.db_models import Permission

rates = dict()

def login_user():
    try:
        from flask_login import current_user

        # return current_user
        return current_identity
    except ImportError:
        abort(HTTPStatus.UNAUTHORIZED, description="User argument not passed")
        #raise ImportError("User argument not passed")


def user_has(permission, get_user=login_user):
    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            acceptable_permissions = Permission.query.filter_by(name=permission).first()
            user_permissions = []
            current_user = get_user()
            for role in current_user.roles:
                user_permissions += role.permissions
            if acceptable_permissions in user_permissions:
                return func(*args, **kwargs)
            else:
                abort(HTTPStatus.FORBIDDEN, description="You do not have access")
        return inner

    return wrapper


def user_is(role, get_user=login_user):
    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            current_user = get_user()
            if role in current_user.roles:
                return func(*args, **kwargs)
            abort(HTTPStatus.FORBIDDEN, description="You do not have access")

        return inner

    return wrapper


def rate_limit(reqs_in_sec, get_user=login_user):
    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            limiter = None
            if reqs_in_sec not in rates.keys():
                rate = RequestRate(reqs_in_sec, DurationEnum.SECOND)
                limiter = Limiter[RedisBucket](rate)
                rates[reqs_in_sec] = limiter
            else:
                limiter = rates.get(reqs_in_sec)

            current_user = get_user()
            with limiter.ratelimit(current_user, delay=True):
                return func(*args, **kwargs)

        return inner

    return wrapper

