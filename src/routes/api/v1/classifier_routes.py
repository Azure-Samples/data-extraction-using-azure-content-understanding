import azure.functions as func
import json
from configs import get_app_config_manager
from controllers.classifier_controller import ClassifierController
from decorators import error_handler
from services.azure_content_understanding_client import AzureContentUnderstandingClient
from utils.constants import AZURE_AI_CONTENT_UNDERSTANDING_USER_AGENT


classifier_routes_bp = func.Blueprint()


@classifier_routes_bp.route(
    route="classifiers/{classifier_id}",
    methods=["PUT", "GET"]
)
@error_handler
def classifier_management(req: func.HttpRequest) -> func.HttpResponse:
    """Create or retrieve a classifier configuration.

    Args:
        req (func.HttpRequest): The request object.

    Returns:
        func.HttpResponse: The response object.
    """
    environment_config = get_app_config_manager().hydrate_config()
    azure_content_understanding_client = AzureContentUnderstandingClient(
        endpoint=environment_config.content_understanding.endpoint.value,
        subscription_key=environment_config.content_understanding.subscription_key.value,
        timeout=environment_config.content_understanding.request_timeout.value,
        x_ms_useragent=AZURE_AI_CONTENT_UNDERSTANDING_USER_AGENT
    )

    classifier_controller = ClassifierController(azure_content_understanding_client)
    classifier_id = req.route_params.get('classifier_id')

    if req.method == "PUT":
        # Create a new classifier
        try:
            classifier_schema = req.get_json()
            if not classifier_schema:
                return func.HttpResponse(
                    json.dumps({"error": "Classifier schema is required"}),
                    status_code=400,
                    headers={"Content-Type": "application/json"}
                )

            result = classifier_controller.create_classifier(classifier_id, classifier_schema)
            return func.HttpResponse(
                json.dumps(result),
                status_code=201,
                headers={"Content-Type": "application/json"}
            )
        except AttributeError:  # Handle errors if JSON body is None
            return func.HttpResponse(
                json.dumps({"error": "Classifier schema is required"}),
                status_code=400,
                headers={"Content-Type": "application/json"}
            )
        except Exception as e:
            return func.HttpResponse(
                json.dumps({"error": str(e)}),
                status_code=500,
                headers={"Content-Type": "application/json"}
            )

    elif req.method == "GET":
        # Retrieve a classifier
        try:
            result = classifier_controller.get_classifier(classifier_id)
            return func.HttpResponse(
                json.dumps(result),
                status_code=200,
                headers={"Content-Type": "application/json"}
            )
        except Exception as e:
            status_code = 404 if "not found" in str(e).lower() else 500
            return func.HttpResponse(
                json.dumps({"error": str(e)}),
                status_code=status_code,
                headers={"Content-Type": "application/json"}
            )
