import logging
from typing import Union
import os
from services.ingest_config_management_service import IngestConfigManagementService
from services.azure_content_understanding_client import AzureContentUnderstandingClient
from services.ingest_lease_documents_service import IngestionCollectionDocumentService
from utils.document_utils import build_config_id
from models.http_error import HTTPError
from models.data_collection_config import DataType, LeaseAgreementCollectionRow
from models.ingestion_models import IngestCollectionDocumentRequest
from .file_cache_manager import FileCacheManager


class IngestLeaseDocumentsController(object):
    _content_understanding_client: AzureContentUnderstandingClient
    _ingestion_collection_document_service: IngestionCollectionDocumentService
    _ingestion_configuration_management_service: IngestConfigManagementService

    def __init__(
        self,
        content_understanding_client: AzureContentUnderstandingClient,
        ingestion_collection_document_service: IngestionCollectionDocumentService,
        ingestion_configuration_management_service: IngestConfigManagementService
    ):
        """Initializes the IngestLeaseDocumentsController.

        Args:
            content_understanding_client (AzureContentUnderstandingClient): The content understanding client.
            ingestion_collection_document_service (IngestionCollectionDocumentService): The ingestion collection document service.
            ingestion_configuration_management_service (IngestConfigManagementService): The ingestion configuration
                management service.
        """
        self._content_understanding_client = content_understanding_client
        self._ingestion_collection_document_service = ingestion_collection_document_service
        self._ingestion_configuration_management_service = ingestion_configuration_management_service
        self._file_cache_manager = FileCacheManager("analyzer_cache", self._is_local_dev_mode())

    def _is_local_dev_mode(self):
        return os.environ.get("ENVIRONMENT") and os.environ.get("ENVIRONMENT").lower() == "local"

    def ingest_documents(self,
                         config_name: str,
                         config_version: str,
                         documents: list[IngestCollectionDocumentRequest]):
        """Processes the documents by ingesting the content understanding output.

        Depending on the JSON configuration, runs the CU analyzer or classifier to get the corresponding
        output to ingest into CosmosDB.

        Args:
            config_name (str): The name of the configuration.
            config_version (str): The version of the configuration.
            documents (list[IngestCollectionDocumentRequest]): The documents to analyze.

        Returns:
            HttpResponse: The response object.
        """
        config = self._load_and_validate_config(config_name, config_version)

        lease_collection_rows: list[LeaseAgreementCollectionRow] = \
            [row for row in config.collection_rows if row.data_type == DataType.LEASE_AGREEMENT]

        for document in documents:
            for collection_row in lease_collection_rows:
                self._ingestion_collection_document_service.clean_empty_document(
                    document.id,
                    config
                )
                if self._ingestion_collection_document_service.is_document_ingested(
                    document.type,
                    document.id,
                    document.filename,
                    config,
                    document.lease_id
                ):
                    logging.warning(
                        f"Lease document {document.lease_id} with id {document.id} and file name {document.filename} "
                        f"with lease config hash {config.lease_config_hash} has already been ingested. Skipping."
                    )
                    continue

                content_understanding_output = None

                if self._is_local_dev_mode():
                    cache_key = self._file_cache_manager.get_cache_key(
                        document.id,
                        document.filename,
                        config.lease_config_hash)
                    content_understanding_output = self._file_cache_manager.read(cache_key)
                    if content_understanding_output is not None:
                        logging.info(f"Loaded content understanding output from file cache for key: {cache_key}")

                is_classifier_enabled = collection_row.classifier is not None and collection_row.classifier.enabled

                # If not already cached, call the appropriate CU API endpoint to get the output to ingest
                if content_understanding_output is None:
                    if is_classifier_enabled:
                        # If classifier is enabled, use the classifier ID from the collection row
                        classifier_id = collection_row.classifier.classifier_id

                        response = self._content_understanding_client.begin_classify_data(
                            classifier_id,
                            document.file_bytes
                        )
                        content_understanding_output = self._content_understanding_client.poll_result(response)
                    else:
                        # Otherwise, use the analyzer ID for ingestion
                        analyzer_id = collection_row.analyzer_id

                        response = self._content_understanding_client.begin_analyze_data(analyzer_id,
                                                                                         document.file_bytes)
                        content_understanding_output = self._content_understanding_client.poll_result(response)

                    # Cache the content understanding output if in local dev mode
                    if self._is_local_dev_mode():
                        self._file_cache_manager.write(cache_key, content_understanding_output)
                        logging.info(f"Cached content understanding output to file for key: {cache_key}")

                # Ingest the content understanding output into CosmosDB using the appropriate service method
                if is_classifier_enabled:
                    self._ingestion_collection_document_service.ingest_classifier_output(
                        document.type,
                        document.id,
                        document.lease_id,
                        document.filename,
                        document.date_of_document,
                        content_understanding_output,
                        config
                    )
                else:
                    self._ingestion_collection_document_service.ingest_analyzer_output(
                        document.type,
                        document.id,
                        document.lease_id,
                        document.filename,
                        document.date_of_document,
                        content_understanding_output,
                        config
                    )

    def _load_and_validate_config(self, config_name: str, config_version: str):
        """Load and validate the configuration."""
        config_id = build_config_id(config_name, config_version)
        config = self._ingestion_configuration_management_service.load_config(config_id)

        if not config:
            raise HTTPError("Configuration not found.", 404)
        return config
