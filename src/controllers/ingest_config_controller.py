import hashlib
import json
import logging
from typing import Optional
from services.ingest_config_management_service import IngestConfigManagementService
from models import FieldDataCollectionConfig, HTTPError
from models.data_collection_config import (
    LeaseAgreementCollectionRow,
    FieldSchema,
    ArrayFieldSchema,
    FieldMappingMethod,
    FieldMappingType
)
from services.azure_content_understanding_client import AzureContentUnderstandingClient
from utils.document_utils import build_config_id


class AnalyzerConstants:
    ANALYZER_TEMPLATE_ID: str = "document-2024-12-01"
    ANALYZER_SCENARIO: str = "document"
    BASE_ANALYZER_ID: str = "prebuilt-documentAnalyzer"  # Base analyzer for document scenarios


class IngestConfigController(object):
    _config_management_service: IngestConfigManagementService
    _azure_content_understanding_client: Optional[AzureContentUnderstandingClient]

    def __init__(
        self,
        config_management_service: IngestConfigManagementService,
        azure_content_understanding_client: Optional[AzureContentUnderstandingClient] = None
    ):
        """Initializes the ConfigController.

        Args:
            config_management_service (IngestConfigManagementService):
                The service responsible for managing ingest configurations.
            azure_content_understanding_client (Optional[AzureContentUnderstandingClient]):
                The client used for interacting with Azure Content Understanding services.
        """
        self._config_management_service = config_management_service
        self._azure_content_understanding_client = azure_content_understanding_client

    def _config_field_schema(self, field: FieldSchema) -> dict:
        """Converts the field schema of the configuration to a dictionary format.

        Args:
            field (FieldSchema): The field schema object.

        Returns:
            dict: The field schema in dictionary format.
        """
        field_data = field.model_dump()
        field_data["type"] = field.type.to_content_understanding_type()
        return {field.name: field_data}

    def _config_array_field_schema(self, field: ArrayFieldSchema) -> dict:
        """Converts the array field schema of the configuration to a dictionary format.

        Args:
            field (ArrayFieldSchema): The array field schema object.

        Returns:
            dict: The array field schema in dictionary format.
        """
        field_type = field.type.value
        field_method = field.method.value
        field_description = field.description
        field_items = {}

        for item in field.items:
            field_items.update(self._config_field_schema(item))

        return {
            field.name: {
                "type": field_type,
                "method": field_method,
                "description": field_description,
                "items": {
                    "type": FieldMappingType.OBJECT,
                    "method": FieldMappingMethod.EXTRACT,
                    "properties": field_items
                }
            }
        }

    def _build_analyzer_template(
        self,
        row: LeaseAgreementCollectionRow,
        project_id: str
    ) -> dict:
        """Builds the analyzer template for the configuration.

        Args:
            row (LeaseAgreementCollectionRow): The lease agreement collection row.
            project_id (str): The project ID.

        Returns:
            dict: The analyzer template in dictionary format.
        """
        res = {}
        for field in row.field_schema:
            if isinstance(field, ArrayFieldSchema):
                res.update(self._config_array_field_schema(field))
            elif isinstance(field, FieldSchema):
                res.update(self._config_field_schema(field))
            else:
                raise HTTPError(f"Unsupported field type: {type(field)}", 400)

        return {
            "baseAnalyzerId": AnalyzerConstants.BASE_ANALYZER_ID,
            "scenario": AnalyzerConstants.ANALYZER_SCENARIO,
            "config": {
                "returnDetails": True,
                "estimateFieldSourceAndConfidence": True
            },
            "tags": {
                "projectId": project_id,
                "templateId": AnalyzerConstants.ANALYZER_TEMPLATE_ID
            },
            "fieldSchema": {
                "fields": res,
            }
        }

    def set_config(
        self,
        config: dict,
        name: str,
        version: str,
        project_id: str
    ):
        """Sets the configuration in the database.

        Args:
            config (dict): The configuration data.
            name (str): The name of the configuration.
            version (str): The version of the configuration.
            project_id (str): The project ID.

        Returns:
            HttpResponse: The response object.
        """
        config_data: FieldDataCollectionConfig
        try:
            config_data = FieldDataCollectionConfig(**config)
        except ValueError as ex:
            logging.error(f"Failed to parse configuration: {ex}")
            raise HTTPError("Invalid JSON data.", 400)

        if config_data.name != name or config_data.version != version:
            raise HTTPError(
                (
                    "Configuration name and version do not match "
                    "the route parameters."
                ),
                400
            )

        lease_agreement_collection_rows = \
            [row for row in config_data.collection_rows if isinstance(row, LeaseAgreementCollectionRow)]

        if lease_agreement_collection_rows:
            self._validate_analyzers_and_create(
                lease_agreement_collection_rows,
                project_id
            )
            self._validate_classifiers(lease_agreement_collection_rows)
            config_data.lease_config_hash = self._generate_lease_config_hash(lease_agreement_collection_rows)

        config_data.id = build_config_id(name, version)
        self._config_management_service.upsert_config(config_data)

    def get_config(self, name: str, version: str):
        """Gets the configuration from the database.

        Args:
            name (str): The name of the configuration.
            version (str): The version of the configuration.

        Returns:
            dict: The configuration data.
        """
        config_id = build_config_id(name, version)
        response = self._config_management_service.load_config(config_id)
        if response:
            return response.model_dump(by_alias=True)

        raise HTTPError("Configuration not found.", 404)

    def _generate_lease_config_hash(self, collection_rows: list[LeaseAgreementCollectionRow]) -> str:
        """Generates a SHA-256 hash for the lease document configurations.

        Args:
            collection_rows (list): The list of lease document configurations.

        Returns:
            str: The SHA-256 hash of the lease document configurations.
        """
        # Create the hash based on the field schemas and classifier IDs
        lease_agreement_data = []

        for row in collection_rows:
            # Create a dictionary containing both field schema and classifier ID
            row_data = {
                "field_schema": row.field_schema,
                "classifier": row.classifier
            }
            lease_agreement_data.append(row_data)

        # Sort field schemas within each row for consistent hashing
        for row_data in lease_agreement_data:
            row_data["field_schema"].sort(key=lambda x: x.name)

        # Sort rows by classifier_id for consistent ordering
        lease_agreement_data.sort(key=lambda x: x["classifier"])

        def custom_serializer(obj):
            if hasattr(obj, "to_dict"):
                return obj.to_dict()
            elif hasattr(obj, "__dict__"):
                return obj.__dict__
            else:
                raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

        serialized_data = json.dumps(lease_agreement_data, default=custom_serializer)
        return hashlib.sha256(serialized_data.encode("utf-8")).hexdigest()

    def _validate_analyzers_and_create(
        self,
        collection_rows: list[LeaseAgreementCollectionRow],
        project_id: str
    ):
        """Validates that all analyzer IDs in the configuration exist.

        Args:
            collection_rows (list): The list of lease document configurations.
            project_id (str): The project ID.

        Raises:
            HTTPError: If any analyzer_id is invalid or does not exist.
        """
        try:
            analyzers = self._azure_content_understanding_client.get_all_analyzers()
            available_analyzer_ids = {analyzer["analyzerId"] for analyzer in analyzers.get("value", [])}
        except Exception as e:
            logging.error(f"Failed to fetch analyzers: {e}")
            raise HTTPError("Unable to validate analyzers due to a service error.", 500)

        for row in collection_rows:
            analyzer_id = row.analyzer_id
            if analyzer_id in available_analyzer_ids:
                continue

            logging.info(f"Creating analyzer with ID: {analyzer_id}...")
            analyzer_template = self._build_analyzer_template(row, project_id)
            logging.info(f"Analyzer template for {analyzer_id}: {analyzer_template}")
            resp = self._azure_content_understanding_client.begin_create_analyzer(
                analyzer_id=analyzer_id,
                analyzer_template=analyzer_template,
            )
            self._azure_content_understanding_client.poll_result(resp)
            logging.info(f"Analyzer with ID: {analyzer_id} created successfully.")

    def _validate_classifiers(
        self,
        collection_rows: list[LeaseAgreementCollectionRow]
    ):
        """Validates that all classifier IDs in the configuration exist.

        Args:
            collection_rows (list): The list of lease document configurations.

        Raises:
            HTTPError: If any classifier_id is invalid or does not exist.
        """
        try:
            classifiers = self._azure_content_understanding_client.get_all_classifiers()
            available_classifier_ids = {classifier["classifierId"] for classifier in classifiers.get("value", [])}
        except Exception as e:
            logging.error(f"Failed to fetch classifiers: {e}")
            raise HTTPError("Unable to validate classifiers due to a service error.", 500)

        for row in collection_rows:
            if row.classifier is None:
                continue

            classifier_id = row.classifier.classifier_id
            if classifier_id not in available_classifier_ids:
                logging.error(f"Classifier {classifier_id} doesn't exist."
                              "Please create the classifier using the PUT /classifier/CLASSIFIER_ID endpoint.")
