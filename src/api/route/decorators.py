"""Auth decorators"""

import logging
from functools import wraps
from http import HTTPStatus

from flask_jwt import current_identity
from flask import abort, request

from models.db_models import Permission
from opentelemetry import trace
from core.tracer import tracer
import inspect
import opentracing


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


def before_request():
    request_id = request.headers.get("X-Request-Id")
    if not request_id:
        raise RuntimeError("request id is required")

    span = trace.get_current_span()
    span.set_attribute("http.request_id", request_id)


'''
def trace_req():
    def decorator(func):
        def wrapper(*args, **kwargs):
            before_request(func.__name__)
            try:
                response = func(*args, **kwargs)
            except Exception as e:
                # after_request_trace(request, error=e)
                raise e
            # else:
                # after_request_trace(request, response)

            return response

        wrapper.__name__ = func.__name__
        return wrapper

    return decorator
'''

class Trac:
    def __init__(self) -> None:
        self.current_trace_id = None

    def trace(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            before_request()
            trace_id = kwargs.pop("trace_id", None)
            ins = inspect.stack()[1][3]
            with tracer.start_as_current_span(ins):
                with tracer.start_as_current_span(func.__name__):
                    print("--hello--")
                    span = trace.get_current_span()
                    span.set_attribute("test", "test")
            if trace_id:
                if self.current_trace_id:
                    raise
                self.current_trace_id = trace_id
                res = func(*args, **kwargs)
                self.current_trace_id = None
                return res
            elif self.current_trace_id:
                return func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        return wrapper
