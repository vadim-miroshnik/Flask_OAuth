"""Auth decorators"""

import logging
from functools import wraps
from http import HTTPStatus

from flask_jwt import current_identity
from flask import abort

from models.db_models import Permission


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

