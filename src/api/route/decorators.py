"""Auth decorators"""

from functools import wraps
from http import HTTPStatus

from flask_jwt import current_identity
from flask import abort, request

from core.settings import settings
from rate_limiter.limiter import Limiter
from rate_limiter.redis_bucket import RedisBucket

from models.db_models import Permission
from opentelemetry import trace
from core.tracer import tracer
import inspect
import opentracing


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


def before_request():
    request_id = request.headers.get("X-Request-Id")
    if not request_id:
        raise RuntimeError("request id is required")

    span = trace.get_current_span()
    span.set_attribute("http.request_id", request_id)


class Trac:
    def __init__(self) -> None:
        self.current_trace_id = None

    def trace(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if settings.disable_trace:
                return func(*args, **kwargs)
            before_request()
            trace_id = kwargs.pop("trace_id", None)
            ins = inspect.stack()[1][3]
            with tracer.start_as_current_span(ins):
                with tracer.start_as_current_span(func.__name__):
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


def rate_limit(reqs_in_sec, get_user=login_user):
    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            if settings.disable_limiter:
                return func(*args, **kwargs)
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
