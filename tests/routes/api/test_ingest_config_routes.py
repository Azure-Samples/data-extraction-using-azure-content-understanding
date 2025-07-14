import unittest
from unittest.mock import patch, Mock
from azure.functions import HttpRequest
import json
from routes.api.v1.ingest_config_routes import (
    ingest_config_management,
    get_default_config
)
from utils.constants import AZURE_AI_CONTENT_UNDERSTANDING_USER_AGENT


class TestIngestConfigManagement(unittest.TestCase):
    """Test the IngestConfigManagementRoute class."""

    @patch("routes.api.v1.ingest_config_routes.AzureContentUnderstandingClient")
    @patch("routes.api.v1.ingest_config_routes.IngestConfigManagementService")
    @patch("routes.api.v1.ingest_config_routes.IngestConfigController")
    @patch("routes.api.v1.ingest_config_routes.get_app_config_manager")
    def test_ingest_config_management_put(self,
                                          mock_app_config_manager,
                                          mock_controller,
                                          mock_service,
                                          mock_azure_content_understanding_client):
        """Test the PUT method of the config_management route with an authorized user."""
        # arrange
        json_body = {
            "name": "test_config",
            "version": "1.0",
            "prompt": "Test prompt",
            "collection_rows": []
        }
        req = HttpRequest(
            method="PUT",
            url="/configs/test_config/versions/1.0",
            route_params={"name": "test_config", "version": "1.0"},
            body=json.dumps(json_body).encode("utf-8")
        )
        mock_controller.return_value.set_config.return_value = None

        # Mock the environment config
        mock_env_config = Mock()
        mock_env_config.content_understanding.endpoint.value = "fake-endpoint"
        mock_env_config.content_understanding.subscription_key.value = "fake-key"
        mock_env_config.content_understanding.request_timeout.value = 30
        mock_env_config.auth_management.enable_authorization.value = 'false'
        mock_app_config_manager.return_value.hydrate_config.return_value = mock_env_config

        # act
        response = ingest_config_management(req)

        # assert
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.headers["Location"],
            "/configs/test_config/versions/1.0"
        )
        mock_azure_content_understanding_client.assert_called_once_with(
            endpoint="fake-endpoint",
            subscription_key="fake-key",
            timeout=30,
            x_ms_useragent=AZURE_AI_CONTENT_UNDERSTANDING_USER_AGENT
        )

    @patch("routes.api.v1.ingest_config_routes.AzureContentUnderstandingClient")
    @patch("routes.api.v1.ingest_config_routes.IngestConfigManagementService")
    @patch("routes.api.v1.ingest_config_routes.IngestConfigController")
    @patch("routes.api.v1.ingest_config_routes.get_app_config_manager")
    def test_ingest_config_management_get(self,
                                          mock_app_config_manager,
                                          mock_controller,
                                          mock_service,
                                          mock_azure_content_understanding_client):
        """Test the GET method of the config_management route with an authorized user."""
        # arrange
        req = HttpRequest(
            method="GET",
            url="/configs/test_config/versions/1.0",
            route_params={"name": "test_config", "version": "1.0"},
            body=None
        )
        mock_controller.return_value.get_config.return_value = {
            "name": "test_config",
            "version": "1.0",
            "lease_config_hash": "fake-hash",
            "prompt": "Test prompt",
            "collection_rows": []
        }

        # Mock the environment config
        mock_env_config = Mock()
        mock_env_config.content_understanding.endpoint.value = "fake-endpoint"
        mock_env_config.content_understanding.subscription_key.value = "fake-key"
        mock_env_config.content_understanding.request_timeout.value = 30
        mock_env_config.auth_management.enable_authorization.value = 'false'
        mock_app_config_manager.return_value.hydrate_config.return_value = mock_env_config

        # act
        response = ingest_config_management(req)

        # assert
        json_body = {
            "name": "test_config",
            "version": "1.0",
            "lease_config_hash": "fake-hash",
            "prompt": "Test prompt",
            "collection_rows": []
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_body(),
            json.dumps(json_body).encode("utf-8")
        )
        mock_azure_content_understanding_client.assert_not_called()


class TestGetDefaultConfig(unittest.TestCase):
    """Test the get_default_config route."""

    @patch("routes.api.v1.ingest_config_routes.AzureContentUnderstandingClient")
    @patch("routes.api.v1.ingest_config_routes.IngestConfigManagementService")
    @patch("routes.api.v1.ingest_config_routes.IngestConfigController")
    @patch("routes.api.v1.ingest_config_routes.get_app_config_manager")
    def test_get_default_config(self,
                                mock_app_config_manager,
                                mock_controller,
                                mock_service,
                                mock_azure_content_understanding_client):
        """Test the GET method of the get_default_config route."""
        # Arrange
        req = HttpRequest(
            method="GET",
            url="/configs/default",
            route_params={},
            body=None
        )

        mock_env_config = Mock()
        mock_env_config.default_ingest_config.name.value = "default_config"
        mock_env_config.default_ingest_config.version.value = "1.0"
        mock_env_config.auth_management.enable_authorization.value = 'false'

        mock_app_config_manager.return_value.hydrate_config.return_value = mock_env_config

        expected_config_data = {
            "name": "default_config",
            "version": "1.0",
            "lease_config_hash": "fake-hash",
            "prompt": "Default prompt",
            "collection_rows": []
        }

        mock_controller.return_value.get_config.return_value = expected_config_data

        # Act
        response = get_default_config(req)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_body(),
            json.dumps(expected_config_data).encode("utf-8")
        )
        self.assertEqual(response.headers["Content-Type"], "application/json")
        mock_controller.return_value.get_config.assert_called_once_with("default_config", "1.0")
        mock_azure_content_understanding_client.assert_not_called()
