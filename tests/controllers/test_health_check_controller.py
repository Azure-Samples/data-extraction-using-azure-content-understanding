from unittest.mock import AsyncMock, MagicMock, patch
from unittest import IsolatedAsyncioTestCase, TestCase
from controllers.health_check_controller import HealthCheckController
from utils.health_check_cache import service_status


class TestHealthCheckControllerPerformHealthChecks(TestCase):
    """Unit tests for the perform_health_checks method in HealthCheckController."""

    def setUp(self):
        """Set up test dependencies."""
        self.mock_config = MagicMock()
        self.mock_config.cosmosdb.db_name.value = "mock_database"
        self.mock_config.cosmosdb.configuration_collection_name.value = "mock_configurations"
        self.mock_config.cosmosdb.leases_collection_name.value = "mock_lease_documents"
        self.mock_config.chat_history.db_name.value = "mock_chat_history_db"
        self.mock_config.chat_history.chat_history_container_name.value = "mock_chat_history_container"
        self.controller = HealthCheckController(self.mock_config)
        service_status["openai"] = None

    def tearDown(self):
        """Reset global state after each test."""
        service_status["openai"] = None

    @patch("utils.health_check_cache.is_cache_valid")
    @patch("utils.health_check_cache.HealthCheckCache.unhealthy_services", new_callable=MagicMock)
    async def test_perform_health_checks_cache_valid_healthy(self, mock_unhealthy_services, mock_is_cache_valid):
        """Test perform_health_checks when cache is valid and status is healthy."""
        mock_is_cache_valid.return_value = True
        mock_unhealthy_services.return_value = []

        result = await self.controller.perform_health_checks()

        self.assertEqual(result["status"], "healthy")
        self.assertIn("checks", result)
        self.assertTrue(all(check["status"] == "healthy" for check in result["checks"].values()))

    @patch("utils.health_check_cache.is_cache_valid")
    @patch("utils.health_check_cache.HealthCheckCache.unhealthy_services", new_callable=MagicMock)
    async def test_perform_health_checks_cache_valid_unhealthy(self, mock_unhealthy_services, mock_is_cache_valid):
        """Test perform_health_checks when cache is valid and status is unhealthy."""
        mock_is_cache_valid.return_value = True
        mock_unhealthy_services.return_value = [{"name": "cosmos_db", "message": "Connection error"}]

        result = await self.controller.perform_health_checks()

        self.assertEqual(result["status"], "unhealthy")
        self.assertIn("checks", result)
        self.assertEqual(result["checks"]["cosmos_db"]["status"], "unhealthy")
        self.assertIn("Connection error", result["checks"]["cosmos_db"]["details"])

    @patch("utils.health_check_cache.is_cache_valid")
    @patch("controllers.health_check_controller.HealthCheckController._run_health_checks", new_callable=AsyncMock)
    async def test_perform_health_checks_cache_invalid_healthy(self, mock_run_health_checks, mock_is_cache_valid):
        """Test perform_health_checks when cache is invalid and status is healthy."""
        mock_is_cache_valid.return_value = False
        mock_run_health_checks.return_value = {
            "status": "healthy",
            "checks": {
                "cosmos_db": {"status": "healthy", "details": "All good"},
                "key_vault": {"status": "healthy", "details": "All good"}
            }
        }

        result = await self.controller.perform_health_checks()

        self.assertEqual(result["status"], "healthy")
        self.assertIn("checks", result)
        self.assertTrue(all(check["status"] == "healthy" for check in result["checks"].values()))

    @patch("utils.health_check_cache.is_cache_valid")
    @patch("controllers.health_check_controller.HealthCheckController._run_health_checks", new_callable=AsyncMock)
    async def test_perform_health_checks_cache_invalid_unhealthy(self, mock_run_health_checks, mock_is_cache_valid):
        """Test perform_health_checks when cache is invalid and status is unhealthy."""
        mock_is_cache_valid.return_value = False
        mock_run_health_checks.return_value = {
            "status": "unhealthy",
            "checks": {
                "cosmos_db": {"status": "unhealthy", "details": "Connection error"},
                "key_vault": {"status": "healthy", "details": "All good"}
            }
        }

        result = await self.controller.perform_health_checks()

        self.assertEqual(result["status"], "unhealthy")
        self.assertIn("checks", result)
        self.assertEqual(result["checks"]["cosmos_db"]["status"], "unhealthy")
        self.assertIn("Connection error", result["checks"]["cosmos_db"]["details"])


class TestHealthCheckControllerHealthChecks(IsolatedAsyncioTestCase):
    """Unit tests for the HealthCheckController."""

    def setUp(self):
        """Set up test dependencies."""
        service_status["openai"] = None
        self.mock_config = MagicMock()
        self.mock_config.cosmosdb.db_name.value = "mock_database"
        self.mock_config.cosmosdb.configuration_collection_name.value = "mock_configurations"
        self.mock_config.cosmosdb.document_collection_name.value = "mock_lease_documents"
        self.mock_config.chat_history.db_name.value = "mock_chat_history_db"
        self.mock_config.chat_history.chat_history_container_name.value = "mock_chat_history_container"
        self.controller = HealthCheckController(self.mock_config)

    @patch("controllers.health_check_controller.CosmosClient")
    async def test_check_mongo_db_success(self, mock_cosmos_client):
        """Test _check_mongo_db method (happy case)."""
        mock_client_instance = mock_cosmos_client.return_value
        mock_client_instance.collection_exists.return_value = True

        result = await self.controller._check_mongo_db()

        self.assertEqual(result["status"], "healthy")
        self.assertIn("mongo_db is running as expected.", result["details"])

        mock_client_instance.collection_exists.assert_any_call("mock_database", "mock_configurations")
        mock_client_instance.collection_exists.assert_any_call("mock_database", "mock_lease_documents")

    @patch("controllers.health_check_controller.CosmosClient")
    async def test_check_mongo_db_failure(self, mock_cosmos_client):
        """Test _check_mongo_db method (failure case)."""
        mock_client_instance = mock_cosmos_client.return_value
        mock_client_instance.collection_exists.side_effect = lambda db, col: col == "mock_configurations"

        result = await self.controller._check_mongo_db()

        self.assertEqual(result["status"], "unhealthy")
        self.assertIn("Collection 'mock_lease_documents' does not exist", result["details"])

        mock_client_instance.collection_exists.assert_any_call("mock_database", "mock_configurations")
        mock_client_instance.collection_exists.assert_any_call("mock_database", "mock_lease_documents")

    @patch("controllers.health_check_controller.CosmosClient2")
    async def test_check_cosmos_db_success(self, mock_cosmos_client):
        """Test _check_cosmos_db method (happy case)."""
        # Mock Cosmos DB client
        mock_client_instance = mock_cosmos_client.return_value
        mock_client_instance.list_databases.return_value = [{"id": "mock_chat_history_db"}]
        mock_database_proxy = mock_client_instance.get_database_client.return_value
        mock_database_proxy.list_containers.return_value = [{"id": "mock_chat_history_container"}]

        result = await self.controller._check_cosmos_db()

        self.assertEqual(result["status"], "healthy")
        self.assertIn("cosmos_db is running as expected.", result["details"])

        mock_client_instance.list_databases.assert_called_once()
        mock_client_instance.get_database_client.assert_called_once_with("mock_chat_history_db")
        mock_database_proxy.list_containers.assert_called_once()

    @patch("controllers.health_check_controller.CosmosClient2")
    async def test_check_cosmos_db_failure(self, mock_cosmos_client):
        """Test _check_cosmos_db method (failure case)."""
        # Mock Cosmos DB client
        mock_client_instance = mock_cosmos_client.return_value
        mock_client_instance.list_databases.return_value = [{"id": "wrong-db"}]

        result = await self.controller._check_cosmos_db()

        self.assertEqual(result["status"], "unhealthy")
        self.assertIn("Database 'mock_chat_history_db' does not exist.", result["details"])

        mock_client_instance.list_databases.assert_called_once()
        mock_client_instance.get_database_client.assert_not_called()
        mock_database_proxy = mock_client_instance.get_database_client.return_value
        mock_database_proxy.list_containers.assert_not_called()

    @patch("controllers.health_check_controller.ManagedIdentityCredential")
    @patch("controllers.health_check_controller.SecretManager")
    async def test_check_key_vault_success(self, mock_secret_manager, mock_credential):
        """Test _check_key_vault method (happy case)."""
        mock_secret_manager_instance = mock_secret_manager.from_url.return_value
        mock_secret_manager_instance.list_secrets.return_value = ["secret1", "secret2"]

        result = await self.controller._check_key_vault()
        self.assertEqual(result["status"], "healthy")
        self.assertIn("key_vault is running as expected.", result["details"])

        mock_secret_manager.from_url.assert_called_once_with(
            self.mock_config.key_vault_uri,
            mock_credential.return_value
        )
        mock_secret_manager_instance.list_secrets.assert_called_once()

    @patch("controllers.health_check_controller.ManagedIdentityCredential")
    @patch("controllers.health_check_controller.SecretManager")
    async def test_check_key_vault_failure(self, mock_secret_manager, mock_credential):
        """Test _check_key_vault method (failure case)."""
        mock_secret_manager.from_url.side_effect = Exception("Key Vault error")

        result = await self.controller._check_key_vault()

        self.assertEqual(result["status"], "unhealthy")
        self.assertIn("Key Vault error", result["details"])

    @patch("controllers.health_check_controller.AzureContentUnderstandingClient")
    async def test_check_content_understanding_success(self, mock_content_client):
        """Test _check_content_understanding method (happy case)."""
        mock_client_instance = mock_content_client.return_value
        mock_client_instance.get_all_analyzers.return_value = ["analyzer1", "analyzer2"]

        result = await self.controller._check_content_understanding()
        self.assertEqual(result["status"], "healthy")
        self.assertIn("content_understanding is running as expected.", result["details"])

        mock_client_instance.get_all_analyzers.assert_called_once()

    @patch("controllers.health_check_controller.AzureContentUnderstandingClient")
    async def test_check_content_understanding_failure(self, mock_content_client):
        """Test _check_content_understanding method (failure case)."""
        mock_content_client.return_value.get_all_analyzers.side_effect = Exception("Content Understanding error")

        result = await self.controller._check_content_understanding()

        self.assertEqual(result["status"], "unhealthy")
        self.assertIn("Content Understanding error", result["details"])

    @patch("controllers.health_check_controller.get_llm_request_manager")
    async def test_check_azure_openai_success(self, mock_llm_manager):
        """Test _check_azure_openai method (happy case)."""
        mock_manager_instance = mock_llm_manager.return_value
        mock_manager_instance.answer_general_question = AsyncMock(return_value="Test Response")

        result = await self.controller._check_azure_openai()

        self.assertEqual(result["status"], "healthy")
        self.assertIn("azure_openai is running as expected.", result["details"])

        mock_manager_instance.answer_general_question.assert_called_once()

    @patch("controllers.health_check_controller.get_llm_request_manager")
    async def test_check_azure_openai_failure(self, mock_llm_manager):
        """Test _check_azure_openai method (failure case)."""
        mock_llm_manager.return_value.answer_general_question.side_effect = Exception("Azure OpenAI error")

        result = await self.controller._check_azure_openai()

        self.assertEqual(result["status"], "unhealthy")
        self.assertIn("Azure OpenAI error", result["details"])
