"""Application"""

from flasgger import Swagger
from flask import Flask, json, jsonify, request
from flask_jwt import JWT
from flask_migrate import Migrate
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from werkzeug.exceptions import HTTPException

from api.route.crud import api_admin_permission, api_admin_role, api_admin_user
from api.route.inter.user import inter_user
from api.route.oauth import google_blueprint
from api.route.users import users_api
from core.db import db
from core.login_manager import authenticate, identity, login_manager
from core.redis import redis
from core.settings import AppSettings, settings


def configure_tracer() -> None:
    trace.set_tracer_provider(
        TracerProvider(resource=Resource.create({SERVICE_NAME: "auth"}))
    )
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(
            JaegerExporter(
                agent_host_name=settings.jaeger.host,
                agent_port=settings.jaeger.port,
            )
        )
    )
    # Чтобы видеть трейсы в консоли
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(ConsoleSpanExporter())
    )


configure_tracer()

app = Flask(__name__, subdomain_matching=True)
FlaskInstrumentor().instrument_app(app)
app.config.from_object(AppSettings)
swagger = Swagger(app)
migrate = Migrate(app, db)

app.register_blueprint(users_api, url_prefix="/api/users")
app.register_blueprint(google_blueprint, url_prefix="/api/users/login")
app.register_blueprint(api_admin_user, url_prefix="/api/admin/user")
app.register_blueprint(api_admin_role, url_prefix="/api/admin/role")
app.register_blueprint(api_admin_permission, url_prefix="/api/admin/permission")
app.register_blueprint(inter_user, url_prefix="/api/inter/user")


@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps(
        {
            "status_code": e.code,
            "error": e.name,
            "description": e.description,
        }
    )
    response.content_type = "application/json"
    return response


@app.before_request
def before_request():
    request_id = request.headers.get("X-Request-Id")
    if not request_id:
        raise RuntimeError("request id is required")


db.init_app(app)
redis.init_app(app)

jwt = JWT(app, authenticate, identity)
login_manager.init_app(app)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
