import unittest
from unittest.mock import Mock, patch
from controllers.classifier_controller import ClassifierController
from services.azure_content_understanding_client import AzureContentUnderstandingClient
from models.http_error import HTTPError


class TestClassifierController(unittest.TestCase):
    """Unit tests for the ClassifierController class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_azure_client = Mock(spec=AzureContentUnderstandingClient)
        self.controller = ClassifierController(self.mock_azure_client)
        self.test_classifier_id = "test-classifier-id"
        self.test_classifier_schema = {
            "description": "Test classifier",
            "categories": {
                "category1": {"description": "Test category 1", "analyzerId": "test-analyzer-id"},
                "category2": {"description": "Test category 2"}
            }
        }

    @patch('controllers.classifier_controller.logging')
    def test_create_classifier_success(self, mock_logging):
        """Test successful classifier creation."""
        # Arrange
        mock_response = Mock()
        self.mock_azure_client.begin_create_classifier.return_value = mock_response
        self.mock_azure_client.poll_result.return_value = {"status": "succeeded"}

        # Act
        result = self.controller.create_classifier(self.test_classifier_id, self.test_classifier_schema)

        # Assert
        self.mock_azure_client.begin_create_classifier.assert_called_once_with(
            self.test_classifier_id, self.test_classifier_schema
        )
        self.mock_azure_client.poll_result.assert_called_once_with(mock_response)

        expected_result = {
            "message": f"Classifier '{self.test_classifier_id}' created successfully",
            "classifier_id": self.test_classifier_id,
            "status": "created"
        }
        self.assertEqual(result, expected_result)

        # Verify logging calls
        mock_logging.info.assert_any_call(f"Creating classifier with ID: {self.test_classifier_id}...")
        mock_logging.info.assert_any_call(f"Classifier {self.test_classifier_id} created successfully")

    @patch('controllers.classifier_controller.logging')
    def test_create_classifier_begin_create_fails(self, mock_logging):
        """Test classifier creation when begin_create_classifier fails."""
        # Arrange
        error_message = "Failed to start classifier creation"
        self.mock_azure_client.begin_create_classifier.side_effect = Exception(error_message)

        # Act & Assert
        with self.assertRaises(HTTPError) as context:
            self.controller.create_classifier(self.test_classifier_id, self.test_classifier_schema)

        self.assertIn("Failed to create classifier", str(context.exception))
        self.assertIn(error_message, str(context.exception))
        self.assertEqual(context.exception.status_code, 500)

        # Verify the poll_result was not called since begin_create_classifier failed
        self.mock_azure_client.poll_result.assert_not_called()

        # Verify error logging
        mock_logging.error.assert_called_once()

    @patch('controllers.classifier_controller.logging')
    def test_create_classifier_poll_result_fails(self, mock_logging):
        """Test classifier creation when poll_result fails."""
        # Arrange
        mock_response = Mock()
        self.mock_azure_client.begin_create_classifier.return_value = mock_response
        error_message = "Operation timed out"
        self.mock_azure_client.poll_result.side_effect = Exception(error_message)

        # Act & Assert
        with self.assertRaises(HTTPError) as context:
            self.controller.create_classifier(self.test_classifier_id, self.test_classifier_schema)

        self.assertIn("Failed to create classifier", str(context.exception))
        self.assertIn(error_message, str(context.exception))
        self.assertEqual(context.exception.status_code, 500)

        # Verify both methods were called
        self.mock_azure_client.begin_create_classifier.assert_called_once()
        self.mock_azure_client.poll_result.assert_called_once_with(mock_response)

    @patch('controllers.classifier_controller.logging')
    def test_get_classifier_success(self, mock_logging):
        """Test successful classifier retrieval."""
        # Arrange
        expected_classifier_data = {
            "classifierId": self.test_classifier_id,
            "description": "Test classifier",
            "status": "ready"
        }
        self.mock_azure_client.get_classifier_detail_by_id.return_value = expected_classifier_data

        # Act
        result = self.controller.get_classifier(self.test_classifier_id)

        # Assert
        self.mock_azure_client.get_classifier_detail_by_id.assert_called_once_with(self.test_classifier_id)
        self.assertEqual(result, expected_classifier_data)

        # Verify logging
        mock_logging.info.assert_called_once_with(f"Retrieved classifier {self.test_classifier_id}")

    @patch('controllers.classifier_controller.logging')
    def test_get_classifier_not_found_404_in_message(self, mock_logging):
        """Test classifier retrieval when classifier not found (404 in error message)."""
        # Arrange
        error_message = "404 Not Found: Classifier does not exist"
        self.mock_azure_client.get_classifier_detail_by_id.side_effect = Exception(error_message)

        # Act & Assert
        with self.assertRaises(HTTPError) as context:
            self.controller.get_classifier(self.test_classifier_id)

        self.assertIn(f"Classifier '{self.test_classifier_id}' not found", str(context.exception))
        self.assertEqual(context.exception.status_code, 404)

        # Verify error logging
        mock_logging.error.assert_called_once()

    @patch('controllers.classifier_controller.logging')
    def test_get_classifier_general_error(self, mock_logging):
        """Test classifier retrieval with general error (not 404)."""
        # Arrange
        error_message = "Internal server error occurred"
        self.mock_azure_client.get_classifier_detail_by_id.side_effect = Exception(error_message)

        # Act & Assert
        with self.assertRaises(HTTPError) as context:
            self.controller.get_classifier(self.test_classifier_id)

        self.assertIn("Failed to retrieve classifier", str(context.exception))
        self.assertIn(error_message, str(context.exception))
        self.assertEqual(context.exception.status_code, 500)
