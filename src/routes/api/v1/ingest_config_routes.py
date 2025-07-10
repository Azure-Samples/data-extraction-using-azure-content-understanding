import azure.functions as func
import json
from services.ingest_config_management_service import IngestConfigManagementService
from configs import get_app_config_manager
from controllers import IngestConfigController
from decorators import error_handler
from services.azure_content_understanding_client import AzureContentUnderstandingClient
from utils.constants import AZURE_AI_CONTENT_UNDERSTANDING_USER_AGENT


ingest_config_routes_bp = func.Blueprint()


@ingest_config_routes_bp.route(
    route="configs/{name}/versions/{version}",
    methods=["PUT", "GET"]
)
@error_handler
def ingest_config_management(req: func.HttpRequest) -> func.HttpResponse:
    """Upload or Get the configuration data.

    Args:
        req (func.HttpRequest): The request object.

    Returns:
        func.HttpResponse: The response object.
    """
    environment_config = get_app_config_manager().hydrate_config()
    config_management_service = IngestConfigManagementService\
        .from_environment_config(environment_config)
    if req.method == "PUT":
        azure_content_understanding_client = AzureContentUnderstandingClient(
            endpoint=environment_config.content_understanding.endpoint.value,
            subscription_key=environment_config.content_understanding.subscription_key.value,
            timeout=environment_config.content_understanding.request_timeout.value,
            x_ms_useragent=AZURE_AI_CONTENT_UNDERSTANDING_USER_AGENT
        )
        config_controller = IngestConfigController(config_management_service, azure_content_understanding_client)

        name = req.route_params.get('name')
        version = req.route_params.get('version')
        config_data = req.get_json()
        config_controller.set_config(
            config_data,
            name,
            version,
            environment_config.content_understanding.project_id.value,
        )
        return func.HttpResponse(
            body="Configuration uploaded successfully.",
            status_code=201,
            headers={
                "Content-Type": "text/plain",
                "Location": f"/configs/{name}/versions/{version}"
            }
        )
    if req.method == "GET":
        config_controller = IngestConfigController(config_management_service)
        name = req.route_params.get('name')
        version = req.route_params.get('version')
        config_data = config_controller.get_config(name, version)
        return func.HttpResponse(
            body=json.dumps(config_data),
            status_code=200,
            headers={"Content-Type": "application/json"}
        )


@ingest_config_routes_bp.route(
    route="configs/default",
    methods=["GET"]
)
@error_handler
def get_default_config(req: func.HttpRequest) -> func.HttpResponse:
    """Gets the default configuration data.

    Args:
        req (func.HttpRequest): The request object.

    Returns:
        func.HttpResponse: The response object.
    """
    env_config = get_app_config_manager().hydrate_config()
    config_management_service = IngestConfigManagementService\
        .from_environment_config(env_config)
    config_controller = IngestConfigController(
        config_management_service,
        None
    )

    config_name = env_config.default_ingest_config.name.value
    config_version = env_config.default_ingest_config.version.value

    config_data = config_controller.get_config(config_name, config_version)
    return func.HttpResponse(
        body=json.dumps(config_data),
        status_code=200,
        headers={"Content-Type": "application/json"}
    )
