import unittest
from unittest.mock import patch, Mock
from azure.functions import HttpRequest
import json
from datetime import date
from routes.api.v1.ingest_documents_routes import ingest_docs
from models.ingestion_models import IngestCollectionDocumentRequest
from utils.constants import AZURE_AI_CONTENT_UNDERSTANDING_USER_AGENT


class TestIngestDocumentsRoutes(unittest.TestCase):
    """Unit tests for ingest documents routes."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_environment_config = Mock()
        self.mock_environment_config.content_understanding.endpoint.value = "https://test-endpoint.com"
        self.mock_environment_config.content_understanding.subscription_key.value = "test-key"
        self.mock_environment_config.content_understanding.request_timeout.value = 30
        self.mock_environment_config.default_ingest_config.name.value = "test-config"
        self.mock_environment_config.default_ingest_config.version.value = "1.0"
    @patch("routes.api.v1.ingest_documents_routes.IngestLeaseDocumentsController")
    @patch("routes.api.v1.ingest_documents_routes.AzureContentUnderstandingClient")
    @patch("routes.api.v1.ingest_documents_routes.IngestionCollectionDocumentService")
    @patch("routes.api.v1.ingest_documents_routes.IngestConfigManagementService")
    @patch("routes.api.v1.ingest_documents_routes.get_app_config_manager")
    def test_ingest_docs_success(self,
                                 mock_app_config_manager,
                                 mock_config_service,
                                 mock_collection_service,
                                 mock_azure_client,
                                 mock_controller):
        """Test successful document ingestion."""
        # Arrange
        mock_app_config_manager.return_value.hydrate_config.return_value = self.mock_environment_config
        mock_config_service.from_environment_config.return_value = Mock()
        mock_collection_service.from_environment_config.return_value = Mock()
        mock_azure_client.return_value = Mock()
        mock_controller.return_value.ingest_documents.return_value = None

        document_body = b"test document content"
        req = HttpRequest(
            method="POST",
            url="/ingest-documents/collection1/lease1/document.pdf",
            route_params={
                "collection_id": "collection1",
                "lease_id": "lease1",
                "document_name": "document.pdf"
            },
            body=document_body
        )

        # Act
        response = ingest_docs(req)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_body().decode(), "Document ingested successfully.")
        
        # Verify Azure client was initialized correctly
        mock_azure_client.assert_called_once_with(
            endpoint="https://test-endpoint.com",
            subscription_key="test-key",
            timeout=30,
            x_ms_useragent=AZURE_AI_CONTENT_UNDERSTANDING_USER_AGENT
        )
        
        # Verify controller was called with correct parameters
        mock_controller.return_value.ingest_documents.assert_called_once()
        call_args = mock_controller.return_value.ingest_documents.call_args
        self.assertEqual(call_args[1]['config_name'], "test-config")
        self.assertEqual(call_args[1]['config_version'], "1.0")
        self.assertEqual(len(call_args[1]['documents']), 1)
        
        # Verify document request was created correctly
        document_request = call_args[1]['documents'][0]
        self.assertEqual(document_request.id, "collection1")
        self.assertEqual(document_request.lease_id, "lease1")
        self.assertEqual(document_request.filename, "document.pdf")
        self.assertEqual(document_request.file_bytes, document_body)
        self.assertEqual(document_request.date_of_document, date.today())

    @patch("routes.api.v1.ingest_documents_routes.IngestLeaseDocumentsController")
    @patch("routes.api.v1.ingest_documents_routes.AzureContentUnderstandingClient")
    @patch("routes.api.v1.ingest_documents_routes.IngestionCollectionDocumentService")
    @patch("routes.api.v1.ingest_documents_routes.IngestConfigManagementService")
    @patch("routes.api.v1.ingest_documents_routes.get_app_config_manager")
    def test_ingest_docs_missing_collection_id(self,
                                                mock_app_config_manager,
                                                mock_config_service,
                                                mock_collection_service,
                                                mock_azure_client,
                                                mock_controller):
        """Test error when collection_id is missing."""
        # Arrange
        mock_app_config_manager.return_value.hydrate_config.return_value = self.mock_environment_config
        mock_config_service.from_environment_config.return_value = Mock()
        mock_collection_service.from_environment_config.return_value = Mock()
        mock_azure_client.return_value = Mock()
        mock_controller.return_value.ingest_documents.return_value = None

        req = HttpRequest(
            method="POST",
            url="/ingest-documents//lease1/document.pdf",
            route_params={
                "collection_id": "",
                "lease_id": "lease1",
                "document_name": "document.pdf"
            },
            body=b"test content"
        )

        # Act
        response = ingest_docs(req)

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertIn("'collection_id', 'lease_id', and 'document_name' must be provided", 
                      response.get_body().decode())

    @patch("routes.api.v1.ingest_documents_routes.IngestLeaseDocumentsController")
    @patch("routes.api.v1.ingest_documents_routes.AzureContentUnderstandingClient")
    @patch("routes.api.v1.ingest_documents_routes.IngestionCollectionDocumentService")
    @patch("routes.api.v1.ingest_documents_routes.IngestConfigManagementService")
    @patch("routes.api.v1.ingest_documents_routes.get_app_config_manager")
    def test_ingest_docs_missing_lease_id(self,
                                                mock_app_config_manager,
                                                mock_config_service,
                                                mock_collection_service,
                                                mock_azure_client,
                                                mock_controller):
        """Test error when lease_id is missing."""
        # Arrange
        mock_app_config_manager.return_value.hydrate_config.return_value = self.mock_environment_config
        mock_config_service.from_environment_config.return_value = Mock()
        mock_collection_service.from_environment_config.return_value = Mock()
        mock_azure_client.return_value = Mock()
        mock_controller.return_value.ingest_documents.return_value = None
        
        req = HttpRequest(
            method="POST",
            url="/ingest-documents/collection1//document.pdf",
            route_params={
                "collection_id": "collection1",
                "lease_id": "",
                "document_name": "document.pdf"
            },
            body=b"test content"
        )

        # Act
        response = ingest_docs(req)

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertIn("'collection_id', 'lease_id', and 'document_name' must be provided", 
                      response.get_body().decode())

    @patch("routes.api.v1.ingest_documents_routes.IngestLeaseDocumentsController")
    @patch("routes.api.v1.ingest_documents_routes.AzureContentUnderstandingClient")
    @patch("routes.api.v1.ingest_documents_routes.IngestionCollectionDocumentService")
    @patch("routes.api.v1.ingest_documents_routes.IngestConfigManagementService")
    @patch("routes.api.v1.ingest_documents_routes.get_app_config_manager")
    def test_ingest_docs_missing_document_name(self,
                                                mock_app_config_manager,
                                                mock_config_service,
                                                mock_collection_service,
                                                mock_azure_client,
                                                mock_controller):
        """Test error when document_name is missing."""
        # Arrange
        mock_app_config_manager.return_value.hydrate_config.return_value = self.mock_environment_config
        mock_config_service.from_environment_config.return_value = Mock()
        mock_collection_service.from_environment_config.return_value = Mock()
        mock_azure_client.return_value = Mock()
        mock_controller.return_value.ingest_documents.return_value = None
        
        req = HttpRequest(
            method="POST",
            url="/ingest-documents/collection1/lease1/",
            route_params={
                "collection_id": "collection1",
                "lease_id": "lease1",
                "document_name": ""
            },
            body=b"test content"
        )

        # Act
        response = ingest_docs(req)

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertIn("'collection_id', 'lease_id', and 'document_name' must be provided", 
                      response.get_body().decode())

    @patch("routes.api.v1.ingest_documents_routes.IngestLeaseDocumentsController")
    @patch("routes.api.v1.ingest_documents_routes.AzureContentUnderstandingClient")
    @patch("routes.api.v1.ingest_documents_routes.IngestionCollectionDocumentService")
    @patch("routes.api.v1.ingest_documents_routes.IngestConfigManagementService")
    @patch("routes.api.v1.ingest_documents_routes.get_app_config_manager")
    def test_ingest_docs_missing_document_body(self,
                                                mock_app_config_manager,
                                                mock_config_service,
                                                mock_collection_service,
                                                mock_azure_client,
                                                mock_controller):
        """Test error when document body is missing."""
        # Arrange
        mock_app_config_manager.return_value.hydrate_config.return_value = self.mock_environment_config
        mock_config_service.from_environment_config.return_value = Mock()
        mock_collection_service.from_environment_config.return_value = Mock()
        mock_azure_client.return_value = Mock()
        mock_controller.return_value.ingest_documents.return_value = None
        
        req = HttpRequest(
            method="POST",
            url="/ingest-documents/collection1/lease1/document.pdf",
            route_params={
                "collection_id": "collection1",
                "lease_id": "lease1",
                "document_name": "document.pdf"
            },
            body=None
        )

        # Act
        response = ingest_docs(req)

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_body().decode(), "No document body provided.")

    @patch("routes.api.v1.ingest_documents_routes.IngestLeaseDocumentsController")
    @patch("routes.api.v1.ingest_documents_routes.AzureContentUnderstandingClient")
    @patch("routes.api.v1.ingest_documents_routes.IngestionCollectionDocumentService")
    @patch("routes.api.v1.ingest_documents_routes.IngestConfigManagementService")
    @patch("routes.api.v1.ingest_documents_routes.get_app_config_manager")
    def test_ingest_docs_empty_document_body(self,
                                                mock_app_config_manager,
                                                mock_config_service,
                                                mock_collection_service,
                                                mock_azure_client,
                                                mock_controller):
        """Test error when document body is empty."""
        # Arrange
        mock_app_config_manager.return_value.hydrate_config.return_value = self.mock_environment_config
        mock_config_service.from_environment_config.return_value = Mock()
        mock_collection_service.from_environment_config.return_value = Mock()
        mock_azure_client.return_value = Mock()
        mock_controller.return_value.ingest_documents.return_value = None

        req = HttpRequest(
            method="POST",
            url="/ingest-documents/collection1/lease1/document.pdf",
            route_params={
                "collection_id": "collection1",
                "lease_id": "lease1",
                "document_name": "document.pdf"
            },
            body=b""
        )

        # Act
        response = ingest_docs(req)

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_body().decode(), "No document body provided.")

    @patch("routes.api.v1.ingest_documents_routes.IngestLeaseDocumentsController")
    @patch("routes.api.v1.ingest_documents_routes.AzureContentUnderstandingClient")
    @patch("routes.api.v1.ingest_documents_routes.IngestionCollectionDocumentService")
    @patch("routes.api.v1.ingest_documents_routes.IngestConfigManagementService")
    @patch("routes.api.v1.ingest_documents_routes.get_app_config_manager")
    def test_ingest_docs_controller_exception(self,
                                              mock_app_config_manager,
                                              mock_config_service,
                                              mock_collection_service,
                                              mock_azure_client,
                                              mock_controller):
        """Test error handling when controller raises an exception."""
        # Arrange
        mock_app_config_manager.return_value.hydrate_config.return_value = self.mock_environment_config
        mock_config_service.from_environment_config.return_value = Mock()
        mock_collection_service.from_environment_config.return_value = Mock()
        mock_azure_client.return_value = Mock()
        mock_controller.return_value.ingest_documents.side_effect = Exception("Controller error")

        document_body = b"test document content"
        req = HttpRequest(
            method="POST",
            url="/ingest-documents/collection1/lease1/document.pdf",
            route_params={
                "collection_id": "collection1",
                "lease_id": "lease1",
                "document_name": "document.pdf"
            },
            body=document_body
        )

        with self.assertRaises(Exception):
            ingest_docs(req)

    @patch("routes.api.v1.ingest_documents_routes.IngestLeaseDocumentsController")
    @patch("routes.api.v1.ingest_documents_routes.AzureContentUnderstandingClient")
    @patch("routes.api.v1.ingest_documents_routes.IngestionCollectionDocumentService")
    @patch("routes.api.v1.ingest_documents_routes.IngestConfigManagementService")
    @patch("routes.api.v1.ingest_documents_routes.get_app_config_manager")
    def test_ingest_docs_with_pdf_file(self,
                                       mock_app_config_manager,
                                       mock_config_service,
                                       mock_collection_service,
                                       mock_azure_client,
                                       mock_controller):
        """Test ingestion with a PDF file."""
        # Arrange
        mock_app_config_manager.return_value.hydrate_config.return_value = self.mock_environment_config
        mock_config_service.from_environment_config.return_value = Mock()
        mock_collection_service.from_environment_config.return_value = Mock()
        mock_azure_client.return_value = Mock()
        mock_controller.return_value.ingest_documents.return_value = None

        # Simulate PDF file content
        pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj"
        req = HttpRequest(
            method="POST",
            url="/ingest-documents/collection1/lease1/lease-agreement.pdf",
            route_params={
                "collection_id": "collection1",
                "lease_id": "lease1",
                "document_name": "lease-agreement.pdf"
            },
            body=pdf_content
        )

        # Act
        response = ingest_docs(req)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_body().decode(), "Document ingested successfully.")
        
        # Verify document request was created with PDF content
        call_args = mock_controller.return_value.ingest_documents.call_args
        document_request = call_args[1]['documents'][0]
        self.assertEqual(document_request.filename, "lease-agreement.pdf")
        self.assertEqual(document_request.file_bytes, pdf_content)

    @patch("routes.api.v1.ingest_documents_routes.IngestLeaseDocumentsController")
    @patch("routes.api.v1.ingest_documents_routes.AzureContentUnderstandingClient")
    @patch("routes.api.v1.ingest_documents_routes.IngestionCollectionDocumentService")
    @patch("routes.api.v1.ingest_documents_routes.IngestConfigManagementService")
    @patch("routes.api.v1.ingest_documents_routes.get_app_config_manager")
    def test_ingest_docs_service_initialization(self,
                                                mock_app_config_manager,
                                                mock_config_service,
                                                mock_collection_service,
                                                mock_azure_client,
                                                mock_controller):
        """Test that all services are properly initialized."""
        # Arrange
        mock_app_config_manager.return_value.hydrate_config.return_value = self.mock_environment_config
        mock_config_service.from_environment_config.return_value = Mock()
        mock_collection_service.from_environment_config.return_value = Mock()
        mock_azure_client.return_value = Mock()
        mock_controller.return_value.ingest_documents.return_value = None

        document_body = b"test document content"
        req = HttpRequest(
            method="POST",
            url="/ingest-documents/collection1/lease1/document.pdf",
            route_params={
                "collection_id": "collection1",
                "lease_id": "lease1",
                "document_name": "document.pdf"
            },
            body=document_body
        )

        # Act
        response = ingest_docs(req)

        # Assert
        self.assertEqual(response.status_code, 200)
        
        # Verify all services were initialized from environment config
        mock_config_service.from_environment_config.assert_called_once_with(self.mock_environment_config)
        mock_collection_service.from_environment_config.assert_called_once_with(self.mock_environment_config)
        
        # Verify controller was initialized with correct dependencies
        mock_controller.assert_called_once()
        call_args = mock_controller.call_args[1]
        self.assertIn('content_understanding_client', call_args)
        self.assertIn('ingestion_collection_document_service', call_args)
        self.assertIn('ingestion_configuration_management_service', call_args)

    @patch("routes.api.v1.ingest_documents_routes.IngestLeaseDocumentsController")
    @patch("routes.api.v1.ingest_documents_routes.AzureContentUnderstandingClient")
    @patch("routes.api.v1.ingest_documents_routes.IngestionCollectionDocumentService")
    @patch("routes.api.v1.ingest_documents_routes.IngestConfigManagementService")
    @patch("routes.api.v1.ingest_documents_routes.get_app_config_manager")
    def test_ingest_docs_with_special_characters_in_params(self,
                                                           mock_app_config_manager,
                                                           mock_config_service,
                                                           mock_collection_service,
                                                           mock_azure_client,
                                                           mock_controller):
        """Test ingestion with special characters in route parameters."""
        # Arrange
        mock_app_config_manager.return_value.hydrate_config.return_value = self.mock_environment_config
        mock_config_service.from_environment_config.return_value = Mock()
        mock_collection_service.from_environment_config.return_value = Mock()
        mock_azure_client.return_value = Mock()
        mock_controller.return_value.ingest_documents.return_value = None

        document_body = b"test document content"
        req = HttpRequest(
            method="POST",
            url="/ingest-documents/collection-123/lease_456/document%20with%20spaces.pdf",
            route_params={
                "collection_id": "collection-123",
                "lease_id": "lease_456",
                "document_name": "document with spaces.pdf"
            },
            body=document_body
        )

        # Act
        response = ingest_docs(req)

        # Assert
        self.assertEqual(response.status_code, 200)
        
        # Verify document request was created with special characters
        call_args = mock_controller.return_value.ingest_documents.call_args
        document_request = call_args[1]['documents'][0]
        self.assertEqual(document_request.id, "collection-123")
        self.assertEqual(document_request.lease_id, "lease_456")
        self.assertEqual(document_request.filename, "document with spaces.pdf")


if __name__ == '__main__':
    unittest.main()