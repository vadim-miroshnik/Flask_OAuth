""""""

from flask import Flask, request, jsonify

#from time import time
#from rate_limiter.limiter import DurationEnum
#from rate_limiter.limiter import Limiter
#from rate_limiter.request_rate import RequestRate
#from rate_limiter.redis_bucket import RedisBucket
#from rate_limiter.redis import redis
from core.settings import AppSettings
from core.redis import redis

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME


def configure_tracer() -> None:
    trace.set_tracer_provider(TracerProvider()) # resource=Resource.create({SERVICE_NAME: "test"})
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(
            JaegerExporter(
                agent_host_name='localhost',
                agent_port=6831,
            )
        )
    )
    # Чтобы видеть трейсы в консоли
    trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))


configure_tracer()

tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("rootSpan"):
    with tracer.start_as_current_span("childSpan"):
        print("Hello World!")

app = Flask(__name__)

app.config.from_object(AppSettings)

redis.init_app(app)

FlaskInstrumentor().instrument_app(app)


@app.before_request
def before_request():
    request_id = request.headers.get("X-Request-Id")
    if not request_id:
        raise RuntimeError("request id is required")


# limiter = Limiter(RequestRate(5, DurationEnum.SECOND), time_function=time)
#limiter = Limiter[RedisBucket](RequestRate(5, DurationEnum.SECOND), time_function=time)


@app.route("/")
#@limiter.ratelimit("test")
def index():
    req = request.headers["X-Request-Id"]
    return req


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
