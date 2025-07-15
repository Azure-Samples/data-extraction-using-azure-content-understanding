import azure.functions as func

from routes.api.v1 import health_check_routes_bp
from routes.api.v1 import ingest_config_routes_bp
from routes.api.v1 import inference_config_routes_bp
from routes.api.v1 import classifier_routes_bp
from routes.api.v1.ingest_documents_routes import ingest_docs_routes_bp
from utils.monitoring_utils import set_up_monitoring

# set_up_monitoring()

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

app.register_functions(health_check_routes_bp)
app.register_functions(ingest_config_routes_bp)
app.register_functions(inference_config_routes_bp)
app.register_functions(ingest_docs_routes_bp)
# app.register_functions(classifier_routes_bp)