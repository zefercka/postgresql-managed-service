import argparse
import logging
import os

from dramatiq.cli import main as dramatiq_main
from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def parse_queue_name():
    parser = argparse.ArgumentParser()

    parser.add_argument("broker_module")
    parser.add_argument("--queues", "--queue", dest="queue", default="default")

    args, _ = parser.parse_known_args()

    return args.queue


if __name__ == "__main__":
    os.environ["DB_DRIVER"] = "postgresql+psycopg2"
    os.environ["REPOSITORY_TYPE"] = "sync"
    os.environ["TF_LOG"] = "DEBUG"

    from app.config import settings

    queue_name = parse_queue_name()

    # Ресурс с метаданными сервиса
    resource = Resource(
        attributes={
            SERVICE_NAME: f"postgresql-managed-service-{queue_name}-worker",
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

    # Автоматическая инструментация библиотек
    SQLAlchemyInstrumentor().instrument()

    logger.info(settings.REPOSITORY_TYPE)

    dramatiq_main()


# python app/run_dramatiq.py app.src.tasks.create_vm_task --queue default --threads 1
