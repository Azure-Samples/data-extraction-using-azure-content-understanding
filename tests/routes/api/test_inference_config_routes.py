import json
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from routes.api.v1.inference_config_routes import query
from models.api.v1 import QueryRequest

import azure.functions as func


class TestInferenceConfigRoutes(unittest.IsolatedAsyncioTestCase):

    @patch("asyncio.run")
    @patch('routes.api.v1.inference_config_routes.get_app_config_manager')
    @patch('routes.api.v1.inference_config_routes.IngestionCollectionDocumentService')
    @patch('routes.api.v1.inference_config_routes.IngestConfigManagementService')
    @patch('routes.api.v1.inference_config_routes.get_llm_request_manager')
    @patch('routes.api.v1.inference_config_routes.InferenceController')
    @patch('routes.api.v1.inference_config_routes.get_cosmos_chat_history')
    async def test_query_success(
        self,
        mock_get_cosmos_chat_history,
        mock_inference_controller,
        mock_get_llm_request_manager,
        mock_ingest_config_management_service,
        mock_lease_docs_service,
        mock_get_app_config_manager,
        mock_asyncio_run,
    ):
        # Arrange
        request_body = {"query": "test query",
                        "cid": "test-correlation-id",
                        "sid": "test-session-id"}
        user_id = "test_user"
        request = func.HttpRequest(
            method="POST",
            url="/api/v1/query",
            route_params=None,
            body=json.dumps(request_body).encode('utf-8'),
            headers={"Content-Type": "application/json", "x-user": user_id},
        )

        mock_get_cosmos_chat_history.return_value = MagicMock()

        mock_environment_config = MagicMock()
        mock_environment_config.default_ingest_config.name.value = "default_config_name"
        mock_environment_config.default_ingest_config.version.value = "default_config_version"
        mock_environment_config.auth_management.user_id_header_name.value = "x-user"
        mock_get_app_config_manager.return_value.hydrate_config.return_value = mock_environment_config

        mock_env_config = MagicMock()
        mock_env_config.auth_management.enable_authorization.value = 'false'

        mock_ingest_config_management_service.from_environment_config.return_value = MagicMock()
        mock_get_llm_request_manager.return_value = MagicMock()
        mock_lease_docs_service.from_environment_config.return_value = MagicMock()

        mock_controller_instance = MagicMock()
        query_request = QueryRequest(**request_body)
        mock_controller_instance.query = AsyncMock(return_value=MagicMock(
            model_dump_json=lambda: '{"response": "test response"}')
        )
        mock_inference_controller.return_value = mock_controller_instance

        # Mock asyncio.run to call the coroutine directly
        async def mock_run(coroutine):
            return await coroutine
        mock_asyncio_run.side_effect = mock_run

        # Act
        response = await query(request)

        # Assert
        mock_get_app_config_manager.return_value.hydrate_config.assert_called_once()
        mock_ingest_config_management_service.from_environment_config.assert_called_once_with(mock_environment_config)
        mock_get_llm_request_manager.assert_called_once()
        mock_inference_controller.assert_called_once_with(
            mock_get_llm_request_manager.return_value,
            mock_ingest_config_management_service.from_environment_config.return_value,
            mock_get_cosmos_chat_history.return_value,
            mock_lease_docs_service.from_environment_config.return_value
        )
        mock_controller_instance.query.assert_called_once_with(
            query_request,
            "default_config_name",
            "default_config_version",
            user_id
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(response.get_body().decode(), '{"response": "test response"}')

    @patch("asyncio.run")
    @patch('routes.api.v1.inference_config_routes.get_app_config_manager')
    async def test_query_invalid_request_body(
        self,
        mock_get_app_config_manager,
        mock_asyncio_run,
    ):
        """Test that an invalid request body raises an HTTPError with status code 400."""
        # Arrange
        invalid_request_body = {"invalid": "data"}  # Missing required fields like "query", "cid", or "sid"
        user_id = "test_user"
        request = func.HttpRequest(
            method="POST",
            url="/api/v1/query",
            route_params=None,
            body=json.dumps(invalid_request_body).encode('utf-8'),
            headers={"Content-Type": "application/json", "x-user": user_id},
        )

        mock_environment_config = MagicMock()
        mock_environment_config.auth_management.user_id_header_name.value = "x-user"
        mock_environment_config.default_ingest_config.name.value = "default_config_name"
        mock_environment_config.default_ingest_config.version.value = "default_config_version"
        mock_get_app_config_manager.return_value.hydrate_config.return_value = mock_environment_config

        mock_env_config = MagicMock()
        mock_env_config.auth_management.enable_authorization.value = 'false'

        # Mock asyncio.run to call the coroutine directly
        async def mock_run(coroutine):
            return await coroutine
        mock_asyncio_run.side_effect = mock_run

        # Act & Assert
        response = await query(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_body().decode(), "Invalid JSON data.")

    @patch("asyncio.run")
    @patch("routes.api.v1.inference_config_routes.get_app_config_manager")
    async def test_query_missing_user_id(
        self,
        mock_get_app_config_manager,
        mock_asyncio_run
    ):
        # Arrange
        request_body = {"query": "test query"}
        request = func.HttpRequest(
            method="POST",
            url="/api/v1/query",
            route_params=None,
            body=json.dumps(request_body).encode('utf-8'),
            headers={"Content-Type": "application/json"},
        )

        mock_environment_config = MagicMock()
        mock_environment_config.auth_management.user_id_header_name.value = "x-user"
        mock_get_app_config_manager.return_value.hydrate_config.return_value = mock_environment_config

        mock_env_config = MagicMock()
        mock_env_config.auth_management.enable_authorization.value = 'false'

        # Mock asyncio.run to call the coroutine directly
        async def mock_run(coroutine):
            return await coroutine
        mock_asyncio_run.side_effect = mock_run

        # Act
        response = await query(request)

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_body().decode(), "User ID header is missing.")
