import json
import azure.functions as func
from decorators import error_handler
from configs.app_config_manager import get_app_config_manager
from controllers.health_check_controller import HealthCheckController

health_check_routes_bp = func.Blueprint()


@health_check_routes_bp.route(
    route="v1/startup",
    methods=["GET"]
)
async def startup(req: func.HttpRequest) -> func.HttpResponse:
    """Startup endpoint to check if the Function App is running.

    Args:
        req (func.HttpRequest): The request object.

    Returns:
        func.HttpResponse: The response object containing the status of the Function App.
    """
    return func.HttpResponse(
        body=json.dumps({"status": "healthy", "details": "Function App is running."}),
        status_code=200,
        headers={"Content-Type": "application/json"}
    )


@health_check_routes_bp.route(
    route="v1/health",
    methods=["GET"]
)
@error_handler
async def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint to validate deployment success and connectivity with critical services.

    Args:
        req (func.HttpRequest): The request object.

    Returns:
        func.HttpResponse: The response object containing health status.
    """
    environment_config = get_app_config_manager().hydrate_config()

    health_controller = HealthCheckController(environment_config)
    health_status = await health_controller.perform_health_checks()

    if health_status['status'] == 'healthy':
        return func.HttpResponse(
            body=json.dumps(health_status),
            status_code=200,
            headers={"Content-Type": "application/json"}
        )
    else:
        return func.HttpResponse(
            body=json.dumps(health_status),
            status_code=503,
            headers={"Content-Type": "application/json"}
        )
