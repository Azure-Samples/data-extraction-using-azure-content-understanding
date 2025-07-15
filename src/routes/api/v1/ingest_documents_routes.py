from datetime import date
import azure.functions as func
import azurefunctions.extensions.bindings.blob as blob
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

# https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-storage-blob-trigger?tabs=python-v2%2Cisolated-process%2Cnodejs-v4%2Cextensionv5&pivots=programming-language-python
# @ingest_docs_routes_bp.blob_trigger(
#     arg_name="client",
#     path="documents/{document_name}",  # TODO: replace with path
#     connection="AzureWebJobsStorage"  # TODO: replace with connection string variable
# )
@ingest_docs_routes_bp.route(
    route="ingest-documents/{document_name}",
    methods=["POST"]
)
@error_handler
def ingest_docs(req: func.HttpRequest) -> func.HttpResponse:
    """Ingests documents using Azure Content Understanding."""
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

    document_name = req.route_params.get('document_name')
    collection_name = "Collection1"
    lease_name = "Lease1"

    config_name = environment_config.default_ingest_config.name.value
    config_version = environment_config.default_ingest_config.version.value

    document_body = req.get_body()

    if not document_body:
        return func.HttpResponse(
            "No document body provided.",
            status_code=400
        )
    
    request = IngestCollectionDocumentRequest(
        id=collection_name,
        filename=document_name,
        file_bytes=document_body,
        date_of_document=date.today(),
        lease_id=lease_name
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

# https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-storage-blob-trigger?tabs=python-v2%2Cisolated-process%2Cnodejs-v4%2Cextensionv5&pivots=programming-language-python
@ingest_docs_routes_bp.blob_trigger(
    arg_name="myblob",
    path="rawdocuments",
    connection="STORAGE_ACCOUNT_CONNECTION_STRING"
)
@error_handler
def ingest_docs_blob(myblob: func.InputStream) -> func.HttpResponse:
    """Ingests documents using Azure Content Understanding."""
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

    document_name = myblob.name
    collection_name = "Collection1"
    lease_name = "Lease4"

    config_name = environment_config.default_ingest_config.name.value
    config_version = environment_config.default_ingest_config.version.value

    document_body = myblob.read()
    
    request = IngestCollectionDocumentRequest(
        id=collection_name,
        filename=document_name,
        file_bytes=document_body,
        date_of_document=date.today(),
        lease_id=lease_name
    )
    documents = [request]

    ingest_lease_documents_controller.ingest_documents(
        config_name=config_name,
        config_version=config_version,
        documents=documents
    )

