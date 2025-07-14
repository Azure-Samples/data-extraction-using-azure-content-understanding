import unittest
from unittest.mock import patch, Mock
from azure.functions import HttpRequest
import json
from routes.api.v1.classifier_routes import (
    classifier_management
)
from utils.constants import AZURE_AI_CONTENT_UNDERSTANDING_USER_AGENT


class TestClassifierManagement(unittest.TestCase):
    """Test the classifier_management route."""

    @patch("routes.api.v1.classifier_routes.AzureContentUnderstandingClient")
    @patch("routes.api.v1.classifier_routes.ClassifierController")
    @patch("routes.api.v1.classifier_routes.get_app_config_manager")
    def test_classifier_management_put(self,
                                       mock_app_config_manager,
                                       mock_controller,
                                       mock_azure_content_understanding_client):
        """Test the PUT method of the classifier_management route with an authorized user."""
        # arrange
        json_body = {
            "description": "Test classifier for unit testing",
            "tags": {
                "createdBy": "test.user@t-mobile.com"
            },
            "splitMode": "auto",
            "categories": {
                "site_or_tower_lease_agreement": {
                    "description": "A legal contract governing the leasing or subleasing of tower or antenna sites",
                    "analyzerId": "lesa-analyzer-experimentalv2"
                },
                "prime_or_ground_lease_agreement": {
                    "description": "A legal contract governing the leasing or subleasing of ground or land"
                }
            }
        }
        req = HttpRequest(
            method="PUT",
            url="/classifiers/test-classifier",
            route_params={"classifier_id": "test-classifier"},
            body=json.dumps(json_body).encode("utf-8")
        )

        expected_result = {
            "message": "Classifier 'test-classifier' created successfully",
            "classifier_id": "test-classifier",
            "status": "created"
        }
        mock_controller.return_value.create_classifier.return_value = expected_result

        # Mock the environment config
        mock_env_config = Mock()
        mock_env_config.content_understanding.endpoint.value = "fake-endpoint"
        mock_env_config.content_understanding.subscription_key.value = "fake-key"
        mock_env_config.content_understanding.request_timeout.value = 30
        mock_env_config.auth_management.enable_authorization.value = 'false'
        mock_app_config_manager.return_value.hydrate_config.return_value = mock_env_config

        # act
        response = classifier_management(req)

        # assert
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        response_data = json.loads(response.get_body().decode())
        self.assertEqual(response_data, expected_result)

        mock_azure_content_understanding_client.assert_called_once_with(
            endpoint="fake-endpoint",
            subscription_key="fake-key",
            timeout=30,
            x_ms_useragent=AZURE_AI_CONTENT_UNDERSTANDING_USER_AGENT
        )
        mock_controller.return_value.create_classifier.assert_called_once_with(
            "test-classifier", json_body
        )

    @patch("routes.api.v1.classifier_routes.ClassifierController")
    @patch("routes.api.v1.classifier_routes.get_app_config_manager")
    def test_classifier_management_put_missing_schema(self,
                                                      mock_app_config_manager,
                                                      mock_controller):
        """Test the PUT method of the classifier_management route with missing schema."""
        # arrange
        req = HttpRequest(
            method="PUT",
            url="/classifiers/test-classifier",
            route_params={"classifier_id": "test-classifier"},
            body=None
        )

        # Mock the environment config
        mock_env_config = Mock()
        mock_env_config.content_understanding.endpoint.value = "fake-endpoint"
        mock_env_config.content_understanding.subscription_key.value = "fake-key"
        mock_env_config.content_understanding.request_timeout.value = 30
        mock_env_config.auth_management.enable_authorization.value = 'false'
        mock_app_config_manager.return_value.hydrate_config.return_value = mock_env_config

        # act
        response = classifier_management(req)

        # assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        response_data = json.loads(response.get_body().decode())
        self.assertEqual(response_data["error"], "Classifier schema is required")

        mock_controller.return_value.create_classifier.assert_not_called()

    @patch("routes.api.v1.classifier_routes.ClassifierController")
    @patch("routes.api.v1.classifier_routes.get_app_config_manager")
    def test_classifier_management_put_empty_schema(self,
                                                    mock_app_config_manager,
                                                    mock_controller):
        """Test the PUT method of the classifier_management route with missing schema."""
        # arrange
        req = HttpRequest(
            method="PUT",
            url="/classifiers/test-classifier",
            route_params={"classifier_id": "test-classifier"},
            body={}
        )

        # Mock the environment config
        mock_env_config = Mock()
        mock_env_config.content_understanding.endpoint.value = "fake-endpoint"
        mock_env_config.content_understanding.subscription_key.value = "fake-key"
        mock_env_config.content_understanding.request_timeout.value = 30
        mock_env_config.auth_management.enable_authorization.value = 'false'
        mock_app_config_manager.return_value.hydrate_config.return_value = mock_env_config

        # act
        response = classifier_management(req)

        # assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        response_data = json.loads(response.get_body().decode())
        self.assertEqual(response_data["error"], "Classifier schema is required")

        mock_controller.return_value.create_classifier.assert_not_called()

    @patch("routes.api.v1.classifier_routes.AzureContentUnderstandingClient")
    @patch("routes.api.v1.classifier_routes.ClassifierController")
    @patch("routes.api.v1.classifier_routes.get_app_config_manager")
    def test_classifier_management_put_controller_exception(self,
                                                            mock_app_config_manager,
                                                            mock_controller,
                                                            mock_azure_content_understanding_client):
        """Test the PUT method when controller raises an exception."""
        # arrange
        json_body = {
            "description": "Test classifier",
            "categories": {"test": {"description": "Test category"}}
        }
        req = HttpRequest(
            method="PUT",
            url="/classifiers/test-classifier",
            route_params={"classifier_id": "test-classifier"},
            body=json.dumps(json_body).encode("utf-8")
        )

        mock_controller.return_value.create_classifier.side_effect = Exception("Creation failed")

        # Mock the environment config
        mock_env_config = Mock()
        mock_env_config.content_understanding.endpoint.value = "fake-endpoint"
        mock_env_config.content_understanding.subscription_key.value = "fake-key"
        mock_env_config.content_understanding.request_timeout.value = 30
        mock_env_config.auth_management.enable_authorization.value = 'false'
        mock_app_config_manager.return_value.hydrate_config.return_value = mock_env_config

        # act
        response = classifier_management(req)

        # assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        response_data = json.loads(response.get_body().decode())
        self.assertEqual(response_data["error"], "Creation failed")

    @patch("routes.api.v1.classifier_routes.AzureContentUnderstandingClient")
    @patch("routes.api.v1.classifier_routes.ClassifierController")
    @patch("routes.api.v1.classifier_routes.get_app_config_manager")
    def test_classifier_management_get(self,
                                       mock_app_config_manager,
                                       mock_controller,
                                       mock_azure_content_understanding_client):
        """Test the GET method of the classifier_management route with an authorized user."""
        # arrange
        req = HttpRequest(
            method="GET",
            url="/classifiers/test-classifier",
            route_params={"classifier_id": "test-classifier"},
            body=None
        )

        expected_classifier_data = {
            "classifierId": "test-classifier",
            "description": "Test classifier for unit testing",
            "tags": {
                "createdBy": "test.user@t-mobile.com"
            },
            "splitMode": "auto",
            "categories": {
                "site_or_tower_lease_agreement": {
                    "description": "A legal contract governing the leasing or subleasing of tower or antenna sites",
                    "analyzerId": "lesa-analyzer-experimentalv2"
                },
                "prime_or_ground_lease_agreement": {
                    "description": "A legal contract governing the leasing or subleasing of ground or land"
                }
            },
            "status": "ready",
            "createdDateTime": "2024-01-01T00:00:00Z"
        }
        mock_controller.return_value.get_classifier.return_value = expected_classifier_data

        # Mock the environment config
        mock_env_config = Mock()
        mock_env_config.content_understanding.endpoint.value = "fake-endpoint"
        mock_env_config.content_understanding.subscription_key.value = "fake-key"
        mock_env_config.content_understanding.request_timeout.value = 30
        mock_env_config.auth_management.enable_authorization.value = 'false'
        mock_app_config_manager.return_value.hydrate_config.return_value = mock_env_config

        # act
        response = classifier_management(req)

        # assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        response_data = json.loads(response.get_body().decode())
        self.assertEqual(response_data, expected_classifier_data)

        mock_azure_content_understanding_client.assert_called_once_with(
            endpoint="fake-endpoint",
            subscription_key="fake-key",
            timeout=30,
            x_ms_useragent=AZURE_AI_CONTENT_UNDERSTANDING_USER_AGENT
        )
        mock_controller.return_value.get_classifier.assert_called_once_with("test-classifier")

    @patch("routes.api.v1.classifier_routes.AzureContentUnderstandingClient")
    @patch("routes.api.v1.classifier_routes.ClassifierController")
    @patch("routes.api.v1.classifier_routes.get_app_config_manager")
    def test_classifier_management_get_not_found(self,
                                                 mock_app_config_manager,
                                                 mock_controller,
                                                 mock_azure_content_understanding_client):
        """Test the GET method when classifier is not found."""
        # arrange
        req = HttpRequest(
            method="GET",
            url="/classifiers/nonexistent-classifier",
            route_params={"classifier_id": "nonexistent-classifier"},
            body=None
        )

        mock_controller.return_value.get_classifier.side_effect = Exception("Classifier not found")

        # Mock the environment config
        mock_env_config = Mock()
        mock_env_config.content_understanding.endpoint.value = "fake-endpoint"
        mock_env_config.content_understanding.subscription_key.value = "fake-key"
        mock_env_config.content_understanding.request_timeout.value = 30
        mock_env_config.auth_management.enable_authorization.value = 'false'
        mock_app_config_manager.return_value.hydrate_config.return_value = mock_env_config

        # act
        response = classifier_management(req)

        # assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        response_data = json.loads(response.get_body().decode())
        self.assertEqual(response_data["error"], "Classifier not found")

    @patch("routes.api.v1.classifier_routes.AzureContentUnderstandingClient")
    @patch("routes.api.v1.classifier_routes.ClassifierController")
    @patch("routes.api.v1.classifier_routes.get_app_config_manager")
    def test_classifier_management_get_server_error(self,
                                                    mock_app_config_manager,
                                                    mock_controller,
                                                    mock_azure_content_understanding_client):
        """Test the GET method when a server error occurs."""
        # arrange
        req = HttpRequest(
            method="GET",
            url="/classifiers/test-classifier",
            route_params={"classifier_id": "test-classifier"},
            body=None
        )

        mock_controller.return_value.get_classifier.side_effect = Exception("Server error occurred")

        # Mock the environment config
        mock_env_config = Mock()
        mock_env_config.content_understanding.endpoint.value = "fake-endpoint"
        mock_env_config.content_understanding.subscription_key.value = "fake-key"
        mock_env_config.content_understanding.request_timeout.value = 30
        mock_env_config.auth_management.enable_authorization.value = 'false'
        mock_app_config_manager.return_value.hydrate_config.return_value = mock_env_config

        # act
        response = classifier_management(req)

        # assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        response_data = json.loads(response.get_body().decode())
        self.assertEqual(response_data["error"], "Server error occurred")


if __name__ == "__main__":
    unittest.main()
