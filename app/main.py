import logging
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
    OTLPMetricExporter,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.src.api.admin import app as admin_controller
from app.src.api.auth.controller import app as auth_controller
from app.src.api.cluster_users.controller import app as cluster_users_controller
from app.src.api.clusters.controller import app as clusters_controller
from app.src.dependency import vault

vault.get_vault_client()

ds = time.time()

# Ресурс с метаданными сервиса
resource = Resource(
    attributes={
        SERVICE_NAME: "postgresql-managed-service",
        SERVICE_VERSION: "1.0.0",
    }
)

# Настройка трейсинга
trace_exporter = OTLPSpanExporter(
    endpoint=settings.OPENTELEMETRY_COLLECTOR_URL_GRPC, insecure=True
)
trace_provider = TracerProvider(resource=resource)
trace_processor = BatchSpanProcessor(trace_exporter)
trace_provider.add_span_processor(trace_processor)
trace.set_tracer_provider(trace_provider)

# Настройка метрик
metric_exporter = OTLPMetricExporter(
    endpoint=settings.OPENTELEMETRY_COLLECTOR_URL_GRPC, insecure=True
)
metric_reader = PeriodicExportingMetricReader(metric_exporter)
metric_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(metric_provider)

# Настройка логирования
log_level = settings.LOG_LEVEL
logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)

log_exporter = OTLPLogExporter(
    endpoint=settings.OPENTELEMETRY_COLLECTOR_URL_GRPC, insecure=True
)
logger_provider = LoggerProvider(resource=resource)
logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
set_logger_provider(logger_provider)

# Подключение OpenTelemetry к logging
handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
logging.getLogger().addHandler(handler)

logger.info(
    f"Starting application in {settings.ENVIRONMENT} mode "
    f"with log level {logging.getLevelName(log_level)}"
)

app = FastAPI()

# Автоматическая инструментация FastAPI
FastAPIInstrumentor.instrument_app(app)

# Автоматическая инструментация SQLAlchemy
SQLAlchemyInstrumentor().instrument()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_controller, tags=["Auth"])
app.include_router(clusters_controller, tags=["Clusters"])
app.include_router(cluster_users_controller, tags=["Cluster Users"])
app.include_router(admin_controller)

logger.info(f"Application started in {time.time() - ds}s")


# uvicorn app.main:app --host=0.0.0.0 --reload
