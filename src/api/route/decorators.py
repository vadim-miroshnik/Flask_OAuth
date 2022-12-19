"""Auth decorators"""

from functools import wraps
from http import HTTPStatus

from flask_jwt import current_identity
from flask import abort

from rate_limiter.limiter import Limiter
from rate_limiter.redis_bucket import RedisBucket

from models.db_models import Permission


class Singleton(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


class Rates(dict, metaclass=Singleton):
    pass


rates = Rates()


def login_user():
    try:
        from flask_login import current_user

        # return current_user
        return current_identity
    except ImportError:
        abort(HTTPStatus.UNAUTHORIZED, description="User argument not passed")


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
            if not (limiter := rates.get(reqs_in_sec)):
                limiter = Limiter[RedisBucket](reqs_in_sec)
                rates[reqs_in_sec] = limiter

            current_user = get_user()
            if not current_user:
                current_user = "Anonymous"

            with limiter.ratelimit(current_user, delay=False):
                return func(*args, **kwargs)

        return inner

    return wrapper

