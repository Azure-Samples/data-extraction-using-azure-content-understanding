import os
import logging
from azure.monitor.opentelemetry.exporter import (
    AzureMonitorLogExporter,
    AzureMonitorMetricExporter,
    AzureMonitorTraceExporter,
)
from opentelemetry._logs import set_logger_provider
from opentelemetry.metrics import set_meter_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.trace import set_tracer_provider
from constants import ENVIRONMENT


_APP_INSIGHTS_CONNECTION_STRING_ENV_VAR_NAME = "APPLICATIONINSIGHTS_CONNECTION_STRING"
_RESOURCE_NAME = f"devdatextwufunc0-{ENVIRONMENT}"


# See this doc as reference for Semantic Kernel telemetry instrumentation
# https://learn.microsoft.com/en-us/semantic-kernel/concepts/enterprise-readiness/observability/telemetry-with-app-insights?tabs=Bash&pivots=programming-language-python


def set_up_logging(connection_string: str, resource: Resource):
    """Configures OTel logging and exporting to Azure Monitor.

    Args:
        connection_string (str): Azure App Insights connection string
        resource (str): associated resource in App Insights
    """
    exporter = AzureMonitorLogExporter(connection_string=connection_string)

    # Create and set a global logger provider for the application.
    logger_provider = LoggerProvider(resource=resource)
    # Log processors are initialized with an exporter which is responsible
    # for sending the telemetry data to a particular backend.
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
    # Sets the global default logger provider
    set_logger_provider(logger_provider)

    # Create a logging handler to write logging records, in OTLP format, to the exporter.
    handler = LoggingHandler()
    # Attach the handler to the logger. `getLogger()` with no arguments returns the root logger.
    # Events from all child loggers will be processed by this handler.
    logger = logging.getLogger(__name__)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def set_up_tracing(connection_string: str, resource: Resource):
    """Configures OTel tracing and exporting to Azure Monitor.

    Args:
        connection_string (str): Azure App Insights connection string
        resource (Resource): associated resource in App Insights
    """
    exporter = AzureMonitorTraceExporter(connection_string=connection_string)

    # Initialize a trace provider for the application. This is a factory for creating tracers.
    tracer_provider = TracerProvider(resource=resource)
    # Span processors are initialized with an exporter which is responsible
    # for sending the telemetry data to a particular backend.
    tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
    # Sets the global default tracer provider
    set_tracer_provider(tracer_provider)


def set_up_metrics(connection_string: str, resource: Resource):
    """Configures OTel metrics and exporting to Azure Monitor.

    Args:
        connection_string (str): Azure App Insights connection string
        resource (Resource): associated resource in App Insights
    """
    exporter = AzureMonitorMetricExporter(
        connection_string=connection_string
    )

    # Initialize a metric provider for the application. This is a factory for creating meters.
    meter_provider = MeterProvider(
        metric_readers=[PeriodicExportingMetricReader(exporter, export_interval_millis=5000)],
        resource=resource,
    )
    # Sets the global default meter provider
    set_meter_provider(meter_provider)


def set_up_monitoring():
    """Configures OTel monitoring for Semantic Kernel instrumentation."""
    app_insights_connection_string = os.environ.get(
        _APP_INSIGHTS_CONNECTION_STRING_ENV_VAR_NAME
    )
    resource_name = _RESOURCE_NAME
    if app_insights_connection_string is None:
        # No monitoring configuration provided
        logging.info("No monitoring configuration provided. Skipping OTel setup.")
        return

    resource = Resource.create({ResourceAttributes.SERVICE_NAME: resource_name})

    set_up_logging(app_insights_connection_string, resource)
    set_up_tracing(app_insights_connection_string, resource)
    set_up_metrics(app_insights_connection_string, resource)
