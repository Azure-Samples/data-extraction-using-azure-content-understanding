import azure.functions as func
import os
from controllers import InferenceController
from decorators import error_handler
from models.api.v1 import QueryRequest
from services.ingest_config_management_service import IngestConfigManagementService
from services.ingest_lease_documents_service import IngestionSiteLeaseService
from services.llm_request_manager import get_llm_request_manager
from services.cosmos_chat_history import get_cosmos_chat_history
from configs import get_app_config_manager

from opentelemetry import trace

inference_config_routes_bp = func.Blueprint()


@inference_config_routes_bp.route(route="v1/query", methods=["POST"])
@error_handler
async def query(req: func.HttpRequest) -> func.HttpResponse:
    """Example function for HTTP trigger.

    Args:
        req (func.HttpRequest): The request object.

    Returns:
        func.HttpResponse: The response object.
    """
    environment_config = get_app_config_manager().hydrate_config()
    user_id = "default"  # req.headers.get(environment_config.auth_management.user_id_header_name.value)
    if not user_id:
        return func.HttpResponse(
            "User ID header is missing.",
            status_code=400
        )

    data = req.get_json()
    config_name = req.params.get('config_name') or environment_config.default_ingest_config.name.value
    config_version = req.params.get('config_version') or environment_config.default_ingest_config.version.value

    try:
        query_request = QueryRequest(**data)
    except ValueError:
        return func.HttpResponse(
            "Invalid JSON data.",
            status_code=400
        )

    env_name = os.getenv('ENVIRONMENT', 'dev')
    session_id = query_request.sid
    correlation_id = query_request.cid

    ingest_config_management_service = IngestConfigManagementService\
        .from_environment_config(environment_config)
    llm_request_manager = get_llm_request_manager()
    chat_history = get_cosmos_chat_history(env_name, environment_config)
    lease_documents_services = IngestionSiteLeaseService.from_environment_config(environment_config)
    controller = InferenceController(
        llm_request_manager,
        ingest_config_management_service,
        chat_history,
        lease_documents_services
    )

    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span(name="query",
                                      attributes={"environment": env_name,
                                                  "correlation-id": correlation_id,
                                                  "session-id": session_id}):
        response = await controller.query(query_request, config_name, config_version, user_id)
        return func.HttpResponse(
            response.model_dump_json(),
            mimetype="application/json",
            status_code=200
        )
