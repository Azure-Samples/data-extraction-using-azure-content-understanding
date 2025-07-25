from datetime import date
import azure.functions as func
import json
from configs.app_config_manager import get_app_config_manager
from controllers import IngestLeaseDocumentsController
from decorators import error_handler
from models.ingestion_models import IngestCollectionDocumentRequest
from services.azure_content_understanding_client import AzureContentUnderstandingClient
from services.ingest_config_management_service import IngestConfigManagementService
from services.ingest_lease_documents_service import IngestionCollectionDocumentService
from utils.constants import AZURE_AI_CONTENT_UNDERSTANDING_USER_AGENT


ingest_docs_routes_bp = func.Blueprint()

@ingest_docs_routes_bp.route(
    route="ingest-documents/{collection_id}/{lease_id}/{document_name}",
    methods=["POST"]
)
@error_handler
def ingest_docs(req: func.HttpRequest) -> func.HttpResponse:
    """Ingests a single document using Azure Content Understanding."""
    environment_config = get_app_config_manager().hydrate_config()
    config_management_service = IngestConfigManagementService\
        .from_environment_config(environment_config)
    collection_document_service = IngestionCollectionDocumentService.\
        from_environment_config(environment_config)
    
    azure_content_understanding_client = AzureContentUnderstandingClient(
        endpoint=environment_config.content_understanding.endpoint.value,
        subscription_key=environment_config.content_understanding.subscription_key.value,
        timeout=environment_config.content_understanding.request_timeout.value,
        x_ms_useragent=AZURE_AI_CONTENT_UNDERSTANDING_USER_AGENT
    )

    ingest_lease_documents_controller = IngestLeaseDocumentsController(
        content_understanding_client=azure_content_understanding_client,
        ingestion_collection_document_service=collection_document_service,
        ingestion_configuration_management_service=config_management_service
    )

    try:
        collection_id = req.route_params.get("collection_id")
        lease_id = req.route_params.get("lease_id")
        document_name = req.route_params.get('document_name')
    except Exception:
        return func.HttpResponse(
            "Missing required path parameters: 'collection_id', 'lease_id', or 'document_name'.",
            status_code=400
        )

    if not collection_id or not lease_id or not document_name:
        return func.HttpResponse(
            "Missing required path parameters: 'collection_id', 'lease_id', or 'document_name'.",
            status_code=400
        )

    config_name = environment_config.default_ingest_config.name.value
    config_version = environment_config.default_ingest_config.version.value

    document_body = req.get_body()

    if not document_body:
        return func.HttpResponse(
            "No document body provided.",
            status_code=400
        )
    
    request = IngestCollectionDocumentRequest(
        id=collection_id,
        filename=document_name,
        file_bytes=document_body,
        date_of_document=date.today(),
        lease_id=lease_id
    )
    documents = [request]

    ingest_lease_documents_controller.ingest_documents(
        config_name=config_name,
        config_version=config_version,
        documents=documents
    )

    return func.HttpResponse(
        body="Document ingested successfully.",
        status_code=200
    )
