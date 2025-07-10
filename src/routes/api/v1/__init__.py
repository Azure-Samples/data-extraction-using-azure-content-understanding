"""Init Package."""
from .health_check_routes import health_check_routes_bp
from .inference_config_routes import inference_config_routes_bp
from .ingest_config_routes import ingest_config_routes_bp
from .classifier_routes import classifier_routes_bp

__all__ = [
    "inference_config_routes_bp",
    "ingest_config_routes_bp",
    "health_check_routes_bp",
    "classifier_routes_bp"
]
