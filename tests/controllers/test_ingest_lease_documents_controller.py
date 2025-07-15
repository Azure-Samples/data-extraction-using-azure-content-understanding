import unittest
from unittest.mock import Mock
from services.ingest_config_management_service import IngestConfigManagementService
from services.azure_content_understanding_client import AzureContentUnderstandingClient
from services.ingest_lease_documents_service import IngestionCollectionDocumentService
from controllers.ingest_lease_documents_controller import IngestLeaseDocumentsController
from models.data_collection_config import FieldDataCollectionConfig
from models.ingestion_models import IngestCollectionDocumentRequest, IngestDocumentType
from models.http_error import HTTPError
from datetime import date


class TestIngestLeaseDocumentsControllerBase(unittest.TestCase):
    def setUp(self):
        """Set up the test case with a mock IngestLeaseDocumentsController."""
        self.mock_content_understanding_client = Mock(spec=AzureContentUnderstandingClient)
        self.mock_ingestion_collection_document_service = Mock(spec=IngestionCollectionDocumentService)
        self.mock_ingestion_configuration_management_service = Mock(spec=IngestConfigManagementService)

        self.controller = IngestLeaseDocumentsController(
            content_understanding_client=self.mock_content_understanding_client,
            ingestion_collection_document_service=self.mock_ingestion_collection_document_service,
            ingestion_configuration_management_service=self.mock_ingestion_configuration_management_service
        )


class TestIngestDocuments(TestIngestLeaseDocumentsControllerBase):
    def test_when_not_ingested_returns_correct_response_analyzer_only(self):
        """Test the ingest_documents method.

        Args:
            self: The test case instance.
        """
        # Arrange
        config_name = "test_config"
        config_version = "1.0"
        documents = [
            IngestCollectionDocumentRequest(
                market="Market",
                id="collection_id_1",
                lease_id="lease_id_1",
                filename="filename_1",
                file_bytes=b"file_bytes_1",
                date_of_document=date(2023, 10, 1),
            ),
            IngestCollectionDocumentRequest(
                market="Market",
                id="collection_id_2",
                lease_id="lease_id_2",
                filename="filename_2",
                file_bytes=b"file_bytes_2",
                date_of_document=date(2023, 10, 1),
            )
        ]
        mock_config = FieldDataCollectionConfig(**{
            "_id": "test_config-1.0",
            "name": "test_config",
            "version": "1.0",
            "prompt": "Test prompt.",
            "lease_config_hash": "test_hash",
            "collection_rows": [
                {
                    "data_type": "LeaseAgreement",
                    "container_name": "lesa",
                    "folder_name": "lease-agreements",
                    "field_schema": [
                        {
                            "name": "earliest_termination_dates",
                            "type": "date",
                            "description": "Earliest termination dates"
                        }
                    ],
                    "analyzer_id": "test-analyzer"
                }
            ]
        })
        mock_analyzer_output = {"analyzer": "output"}

        self.mock_ingestion_collection_document_service.is_document_ingested.return_value = False
        self.mock_ingestion_configuration_management_service.load_config.return_value = mock_config
        self.mock_content_understanding_client.begin_analyze_data.return_value = Mock()
        self.mock_content_understanding_client.poll_result.return_value = mock_analyzer_output

        # Act
        self.controller.ingest_documents(config_name, config_version, documents)

        # Assert
        self.mock_ingestion_configuration_management_service.load_config.assert_called_once_with(
            f"{config_name}-{config_version}"
        )
        self.assertEqual(self.mock_content_understanding_client.begin_analyze_data.call_count, len(documents))
        self.assertEqual(self.mock_content_understanding_client.poll_result.call_count, len(documents))
        self.assertEqual(self.mock_ingestion_collection_document_service.ingest_analyzer_output.call_count, len(documents))

        for document in documents:
            self.mock_content_understanding_client.begin_analyze_data.assert_any_call(
                "test-analyzer", document.file_bytes
            )
            self.mock_ingestion_collection_document_service.ingest_analyzer_output.assert_any_call(
                IngestDocumentType.COLLECTION,
                document.market,
                document.id,
                document.lease_id,
                document.filename,
                document.date_of_document,
                mock_analyzer_output,
                mock_config
            )

    def test_when_already_ingested_returns_correct_response_analyzer_only(self):
        """Test the ingest_documents method.

        Args:
            self: The test case instance.
        """
        # Arrange
        config_name = "test_config"
        config_version = "1.0"
        documents = [
            IngestCollectionDocumentRequest(
                market="Market",
                id="collection_id_1",
                lease_id="lease_id_1",
                filename="filename_1",
                file_bytes=b"file_bytes_1",
                date_of_document=date(2023, 10, 1),
            ),
            IngestCollectionDocumentRequest(
                market="Market",
                id="collection_id_2",
                lease_id="lease_id_2",
                filename="filename_2",
                file_bytes=b"file_bytes_2",
                date_of_document=date(2023, 10, 1),
            )
        ]
        mock_config = FieldDataCollectionConfig(**{
            "_id": "test_config-1.0",
            "name": "test_config",
            "version": "1.0",
            "prompt": "Test prompt.",
            "lease_config_hash": "test_hash",
            "collection_rows": [
                {
                    "data_type": "LeaseAgreement",
                    "container_name": "lesa",
                    "folder_name": "lease-agreements",
                    "field_schema": [
                        {
                            "name": "earliest_termination_dates",
                            "type": "date",
                            "description": "Earliest termination dates"
                        }
                    ],
                    "analyzer_id": "test-analyzer"
                }
            ]
        })
        mock_analyzer_output = {"analyzer": "output"}

        self.mock_ingestion_collection_document_service.is_document_ingested.return_value = True
        self.mock_ingestion_configuration_management_service.load_config.return_value = mock_config
        self.mock_content_understanding_client.begin_analyze_data.return_value = Mock()
        self.mock_content_understanding_client.poll_result.return_value = mock_analyzer_output

        # Act
        self.controller.ingest_documents(config_name, config_version, documents)

        # Assert
        self.mock_ingestion_configuration_management_service.load_config.assert_called_once_with(
            f"{config_name}-{config_version}"
        )

        self.mock_content_understanding_client.begin_analyze_data.assert_not_called()
        self.mock_content_understanding_client.poll_result.assert_not_called()
        self.mock_ingestion_collection_document_service.ingest_analyzer_output.assert_not_called()

    def test_when_config_not_found_raises_exception_analyzer_only(self):
        """Test the ingest_documents method when the config is not found.

        Args:
            self: The test case instance.
        """
        # Arrange
        config_name = "test_config"
        config_version = "1.0"
        documents = [
            IngestCollectionDocumentRequest(
                market="Market",
                id="collection_id_1",
                lease_id="lease_id_1",
                filename="filename_1",
                file_bytes=b"file_bytes_1",
                date_of_document=date(2023, 10, 1),
            )
        ]

        self.mock_ingestion_configuration_management_service.load_config.return_value = None

        # Act & Assert
        with self.assertRaises(HTTPError) as context:
            self.controller.ingest_documents(config_name, config_version, documents)

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(str(context.exception), "Configuration not found.")

    def test_when_not_ingested_returns_correct_response_classifier_enabled(self):
        """Test the ingest_documents method with classifier enabled.

        Args:
            self: The test case instance.
        """
        # Arrange
        config_name = "test_config"
        config_version = "1.0"
        documents = [
            IngestCollectionDocumentRequest(
                market="Market",
                id="collection_id_1",
                lease_id="lease_id_1",
                filename="filename_1",
                file_bytes=b"file_bytes_1",
                date_of_document=date(2023, 10, 1),
            ),
            IngestCollectionDocumentRequest(
                market="Market",
                id="collection_id_2",
                lease_id="lease_id_2",
                filename="filename_2",
                file_bytes=b"file_bytes_2",
                date_of_document=date(2023, 10, 1),
            )
        ]
        mock_config = FieldDataCollectionConfig(**{
            "_id": "test_config-1.0",
            "name": "test_config",
            "version": "1.0",
            "prompt": "Test prompt.",
            "lease_config_hash": "test_hash",
            "collection_rows": [
                {
                    "data_type": "LeaseAgreement",
                    "container_name": "lesa",
                    "folder_name": "lease-agreements",
                    "field_schema": [
                        {
                            "name": "earliest_termination_dates",
                            "type": "date",
                            "description": "Earliest termination dates"
                        }
                    ],
                    "analyzer_id": "test-analyzer",
                    "classifier": {
                        "enabled": True,
                        "classifier_id": "test-classifier"
                    }
                }
            ]
        })
        mock_classifier_output = {"classifier": "output"}

        self.mock_ingestion_collection_document_service.is_document_ingested.return_value = False
        self.mock_ingestion_configuration_management_service.load_config.return_value = mock_config
        self.mock_content_understanding_client.begin_classify_data.return_value = Mock()
        self.mock_content_understanding_client.poll_result.return_value = mock_classifier_output

        # Act
        self.controller.ingest_documents(config_name, config_version, documents)

        # Assert
        self.mock_ingestion_configuration_management_service.load_config.assert_called_once_with(
            f"{config_name}-{config_version}"
        )
        self.assertEqual(self.mock_content_understanding_client.begin_classify_data.call_count, len(documents))
        self.assertEqual(self.mock_content_understanding_client.poll_result.call_count, len(documents))
        classifier_output_call_count = self.mock_ingestion_collection_document_service.ingest_classifier_output.call_count
        self.assertEqual(classifier_output_call_count, len(documents))

        # Verify analyzer methods are not called when classifier is enabled
        self.mock_content_understanding_client.begin_analyze_data.assert_not_called()
        self.mock_ingestion_collection_document_service.ingest_analyzer_output.assert_not_called()

        for document in documents:
            self.mock_content_understanding_client.begin_classify_data.assert_any_call(
                "test-classifier", document.file_bytes
            )
            self.mock_ingestion_collection_document_service.ingest_classifier_output.assert_any_call(
                IngestDocumentType.COLLECTION,
                document.market,
                document.id,
                document.lease_id,
                document.filename,
                document.date_of_document,
                mock_classifier_output,
                mock_config
            )

    def test_when_already_ingested_returns_correct_response_classifier_enabled(self):
        """Test the ingest_documents method when documents are already ingested with classifier enabled.

        Args:
            self: The test case instance.
        """
        # Arrange
        config_name = "test_config"
        config_version = "1.0"
        documents = [
            IngestCollectionDocumentRequest(
                market="Market",
                id="collection_id_1",
                lease_id="lease_id_1",
                filename="filename_1",
                file_bytes=b"file_bytes_1",
                date_of_document=date(2023, 10, 1),
            ),
            IngestCollectionDocumentRequest(
                market="Market",
                id="collection_id_2",
                lease_id="lease_id_2",
                filename="filename_2",
                file_bytes=b"file_bytes_2",
                date_of_document=date(2023, 10, 1),
            )
        ]
        mock_config = FieldDataCollectionConfig(**{
            "_id": "test_config-1.0",
            "name": "test_config",
            "version": "1.0",
            "prompt": "Test prompt.",
            "lease_config_hash": "test_hash",
            "collection_rows": [
                {
                    "data_type": "LeaseAgreement",
                    "container_name": "lesa",
                    "folder_name": "lease-agreements",
                    "field_schema": [
                        {
                            "name": "earliest_termination_dates",
                            "type": "date",
                            "description": "Earliest termination dates"
                        }
                    ],
                    "analyzer_id": "test-analyzer",
                    "classifier": {
                        "enabled": True,
                        "classifier_id": "test-classifier"
                    }
                }
            ]
        })
        mock_classifier_output = {"classifier": "output"}

        self.mock_ingestion_collection_document_service.is_document_ingested.return_value = True
        self.mock_ingestion_configuration_management_service.load_config.return_value = mock_config
        self.mock_content_understanding_client.begin_classify_data.return_value = Mock()
        self.mock_content_understanding_client.poll_result.return_value = mock_classifier_output

        # Act
        self.controller.ingest_documents(config_name, config_version, documents)

        # Assert
        self.mock_ingestion_configuration_management_service.load_config.assert_called_once_with(
            f"{config_name}-{config_version}"
        )

        # Verify neither classifier nor analyzer methods are called when documents are already ingested
        self.mock_content_understanding_client.begin_classify_data.assert_not_called()
        self.mock_content_understanding_client.begin_analyze_data.assert_not_called()
        self.mock_content_understanding_client.poll_result.assert_not_called()
        self.mock_ingestion_collection_document_service.ingest_classifier_output.assert_not_called()
        self.mock_ingestion_collection_document_service.ingest_analyzer_output.assert_not_called()

    def test_when_classifier_disabled_uses_analyzer_path(self):
        """Test that when classifier is present but disabled, the analyzer path is used.

        Args:
            self: The test case instance.
        """
        # Arrange
        config_name = "test_config"
        config_version = "1.0"
        documents = [
            IngestCollectionDocumentRequest(
                market="Market",
                id="collection_id_1",
                lease_id="lease_id_1",
                filename="filename_1",
                file_bytes=b"file_bytes_1",
                date_of_document=date(2023, 10, 1),
            )
        ]
        mock_config = FieldDataCollectionConfig(**{
            "_id": "test_config-1.0",
            "name": "test_config",
            "version": "1.0",
            "prompt": "Test prompt.",
            "lease_config_hash": "test_hash",
            "collection_rows": [
                {
                    "data_type": "LeaseAgreement",
                    "container_name": "lesa",
                    "folder_name": "lease-agreements",
                    "field_schema": [
                        {
                            "name": "earliest_termination_dates",
                            "type": "date",
                            "description": "Earliest termination dates"
                        }
                    ],
                    "analyzer_id": "test-analyzer",
                    "classifier": {
                        "enabled": False,
                        "classifier_id": "test-classifier"
                    }
                }
            ]
        })
        mock_analyzer_output = {"analyzer": "output"}

        self.mock_ingestion_collection_document_service.is_document_ingested.return_value = False
        self.mock_ingestion_configuration_management_service.load_config.return_value = mock_config
        self.mock_content_understanding_client.begin_analyze_data.return_value = Mock()
        self.mock_content_understanding_client.poll_result.return_value = mock_analyzer_output

        # Act
        self.controller.ingest_documents(config_name, config_version, documents)

        # Assert
        self.mock_ingestion_configuration_management_service.load_config.assert_called_once_with(
            f"{config_name}-{config_version}"
        )

        # Verify analyzer methods are called when classifier is disabled
        self.mock_content_understanding_client.begin_analyze_data.assert_called_once_with(
            "test-analyzer", documents[0].file_bytes
        )
        self.mock_ingestion_collection_document_service.ingest_analyzer_output.assert_called_once_with(
            IngestDocumentType.COLLECTION,
            documents[0].market,
            documents[0].id,
            documents[0].lease_id,
            documents[0].filename,
            documents[0].date_of_document,
            mock_analyzer_output,
            mock_config
        )

        # Verify classifier methods are not called when classifier is disabled
        self.mock_content_understanding_client.begin_classify_data.assert_not_called()
        self.mock_ingestion_collection_document_service.ingest_classifier_output.assert_not_called()
