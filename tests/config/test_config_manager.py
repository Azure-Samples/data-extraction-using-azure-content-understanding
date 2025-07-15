from unittest import TestCase
from unittest.mock import MagicMock, patch
import os
from models.environment_config import (
    EnvironmentConfig,
    UserManagedIdentityConfig,
    CosmosDbConfig,
    LLMConfig,
    ConfigurationValue,
    DefaultIngestConfig,
    ContentUnderstandingConfig,
    ChatHistoryConfig,
    BlobStorageConfig
)
import configs.app_config_manager as AppConfigManager


class TestHydrateConfig(TestCase):
    def test_happy_path_not_hydrated_with_kv(self):
        """Test function for hydrate_config."""
        # arrange
        input_env_config = EnvironmentConfig(
            key_vault_uri="https://test.vault.azure.net/",
            tenant_id="tenand_id",
            user_managed_identity=UserManagedIdentityConfig(
                client_id=ConfigurationValue(
                    value="d4fd5faf-ba63-4981-93f4-43b9314c6bd1",
                    type="value"
                )
            ),
            cosmosdb=CosmosDbConfig(
                db_name=ConfigurationValue(
                    value="test_db",
                    type="value"
                ),
                endpoint=ConfigurationValue(
                    value="https://test.endpoint.com",
                    type="value"
                ),
                configuration_collection_name=ConfigurationValue(
                    value="test_collection",
                    type="value"
                ),
                document_collection_name=ConfigurationValue(
                    value="test_collection",
                    type="value"
                ),
            ),
            llm=LLMConfig(
                model_name=ConfigurationValue(
                    value="gpt-4o",
                    type="value"
                ),
                endpoint=ConfigurationValue(
                    value="https://fake.azure.openai.endpoint.com",
                    type="value"
                ),
                access_key=ConfigurationValue(
                    key="OPEN_AI_ACCESS_KEY",
                    type="secret"
                ),
                api_version=ConfigurationValue(
                    value="2025-08-01-preview",
                    type="value"
                ),
                use_request_ca_bundle=ConfigurationValue(
                    value="False",
                    type="value"
                )
            ),
            default_ingest_config=DefaultIngestConfig(
                name=ConfigurationValue(
                    value="test_name",
                    type="value"
                ),
                version=ConfigurationValue(
                    value="1.0.0",
                    type="value"
                )
            ),
            content_understanding=ContentUnderstandingConfig(
                endpoint=ConfigurationValue(
                    value="https://test.endpoint.com",
                    type="value"
                ),
                subscription_key=ConfigurationValue(
                    value="test_subscription_key",
                    type="value"
                ),
                request_timeout=ConfigurationValue[int](
                    value=30,
                    type="value"
                ),
                project_id=ConfigurationValue(
                    value="test_project_id",
                    type="value"
                ),
            ),
            chat_history=ChatHistoryConfig(
                endpoint=ConfigurationValue(
                    value="https://test.endpoint.com",
                    type="value"
                ),
                key=ConfigurationValue(
                    value="test_subscription_key",
                    type="value"
                ),
                db_name=ConfigurationValue(
                    value="test_db",
                    type="value"
                ),
                chat_history_container_name=ConfigurationValue(
                    value="test_collection",
                    type="value"
                ),
                user_message_limit=ConfigurationValue[int](
                    value=1,
                    type="value"
                ),
                domain=ConfigurationValue(
                    value="test_domain",
                    type="value"
                ),
                subdomain=ConfigurationValue(
                    value="test_subdomain",
                    type="value"
                )
            ),
            blob_storage=BlobStorageConfig(
                account_url=ConfigurationValue(
                    value="test_account_url",
                    type="value"
                ),
                container_name=ConfigurationValue(
                    value="test_container_name",
                    type="value"
                )
            )
        )

        expected_env_config = EnvironmentConfig(
            key_vault_uri="https://test.vault.azure.net/",
            tenant_id="tenand_id",
            user_managed_identity=UserManagedIdentityConfig(
                client_id=ConfigurationValue(
                    value="d4fd5faf-ba63-4981-93f4-43b9314c6bd1",
                    type="value"
                )
            ),
            cosmosdb=CosmosDbConfig(
                db_name=ConfigurationValue(
                    value="test_db",
                    type="value"
                ),
                endpoint=ConfigurationValue(
                    value="https://test.endpoint.com",
                    type="value"
                ),
                configuration_collection_name=ConfigurationValue(
                    value="test_collection",
                    type="value"
                ),
                document_collection_name=ConfigurationValue(
                    value="test_collection",
                    type="value"
                )
            ),
            llm=LLMConfig(
                model_name=ConfigurationValue(
                    value="gpt-4o",
                    type="value"
                ),
                endpoint=ConfigurationValue(
                    value="https://fake.azure.openai.endpoint.com",
                    type="value"
                ),
                access_key=ConfigurationValue(
                    key="OPEN_AI_ACCESS_KEY",
                    value="test_access_key",
                    type="secret"
                ),
                api_version=ConfigurationValue(
                    value="2025-08-01-preview",
                    type="value"
                ),
                use_request_ca_bundle=ConfigurationValue(
                    value="False",
                    type="value"
                )
            ),
            default_ingest_config=DefaultIngestConfig(
                name=ConfigurationValue(
                    value="test_name",
                    type="value"
                ),
                version=ConfigurationValue(
                    value="1.0.0",
                    type="value"
                )
            ),
            content_understanding=ContentUnderstandingConfig(
                endpoint=ConfigurationValue(
                    value="https://test.endpoint.com",
                    type="value"
                ),
                subscription_key=ConfigurationValue(
                    value="test_subscription_key",
                    type="value"
                ),
                request_timeout=ConfigurationValue[int](
                    value=30,
                    type="value"
                ),
                project_id=ConfigurationValue(
                    value="test_project_id",
                    type="value"
                )
            ),
            chat_history=ChatHistoryConfig(
                endpoint=ConfigurationValue(
                    value="https://test.endpoint.com",
                    type="value"
                ),
                key=ConfigurationValue(
                    value="test_subscription_key",
                    type="value"
                ),
                db_name=ConfigurationValue(
                    value="test_db",
                    type="value"
                ),
                chat_history_container_name=ConfigurationValue(
                    value="test_collection",
                    type="value"
                ),
                user_message_limit=ConfigurationValue[int](
                    value=1,
                    type="value"
                ),
                domain=ConfigurationValue(
                    value="test_domain",
                    type="value"
                ),
                subdomain=ConfigurationValue(
                    value="test_subdomain",
                    type="value"
                )
            ),
            blob_storage=BlobStorageConfig(
                account_url=ConfigurationValue(
                    value="test_account_url",
                    type="value"
                ),
                container_name=ConfigurationValue(
                    value="test_container_name",
                    type="value"
                )
            )
        )

        def mock_secret_manager_side_effect(secret_name: str) -> str:
            if secret_name == "OPEN_AI_ACCESS_KEY":
                return "test_access_key"
            elif secret_name == "TEST-KEY":
                return "key"
            elif secret_name == "APPLICATIONINSIGHTS_CONNECTION_STRING":
                return "test-connection-string"
            return

        mock_secret_manager = MagicMock()
        mock_secret_manager.get_secret_value.side_effect = mock_secret_manager_side_effect

        app_config_manager = AppConfigManager.AppConfigManager(
            input_env_config,
            mock_secret_manager
        )

        # act
        result = app_config_manager.hydrate_config()

        # assert
        assert result == expected_env_config

    @patch.dict(os.environ, {
        "OPEN_AI_ACCESS_KEY": "test_access_key",
        "TEST-KEY": "key",
        "APPLICATIONINSIGHTS_CONNECTION_STRING": "test-connection-string"
    }, clear=True)
    def test_happy_path_not_hydrated_with_os(self):
        """Test function for hydrate_config."""
        # arrange
        input_env_config = EnvironmentConfig(
            key_vault_uri="https://test.vault.azure.net/",
            tenant_id="tenand_id",
            user_managed_identity=UserManagedIdentityConfig(
                client_id=ConfigurationValue(
                    value="d4fd5faf-ba63-4981-93f4-43b9314c6bd1",
                    type="value"
                )
            ),
            cosmosdb=CosmosDbConfig(
                db_name=ConfigurationValue(
                    value="test_db",
                    type="value"
                ),
                endpoint=ConfigurationValue(
                    value="https://test.endpoint.com",
                    type="value"
                ),
                configuration_collection_name=ConfigurationValue(
                    value="test_collection",
                    type="value"
                ),
                document_collection_name=ConfigurationValue(
                    value="test_collection",
                    type="value"
                ),
            ),
            llm=LLMConfig(
                model_name=ConfigurationValue(
                    value="gpt-4o",
                    type="value"
                ),
                endpoint=ConfigurationValue(
                    value="https://fake.azure.openai.endpoint.com",
                    type="value"
                ),
                access_key=ConfigurationValue(
                    key="OPEN_AI_ACCESS_KEY",
                    type="secret"
                ),
                api_version=ConfigurationValue(
                    value="2025-08-01-preview",
                    type="value"
                ),
                use_request_ca_bundle=ConfigurationValue(
                    value="False",
                    type="value"
                )
            ),
            default_ingest_config=DefaultIngestConfig(
                name=ConfigurationValue(
                    value="test_name",
                    type="value"
                ),
                version=ConfigurationValue(
                    value="1.0.0",
                    type="value"
                )
            ),
            content_understanding=ContentUnderstandingConfig(
                endpoint=ConfigurationValue(
                    value="https://test.endpoint.com",
                    type="value"
                ),
                subscription_key=ConfigurationValue(
                    value="test_subscription_key",
                    type="value"
                ),
                request_timeout=ConfigurationValue[int](
                    value=30,
                    type="value"
                ),
                project_id=ConfigurationValue(
                    value="test_project_id",
                    type="value"
                ),
            ),
            chat_history=ChatHistoryConfig(
                endpoint=ConfigurationValue(
                    value="https://test.endpoint.com",
                    type="value"
                ),
                key=ConfigurationValue(
                    value="test_subscription_key",
                    type="value"
                ),
                db_name=ConfigurationValue(
                    value="test_db",
                    type="value"
                ),
                chat_history_container_name=ConfigurationValue(
                    value="test_collection",
                    type="value"
                ),
                user_message_limit=ConfigurationValue[int](
                    value=1,
                    type="value"
                ),
                domain=ConfigurationValue(
                    value="test_domain",
                    type="value"
                ),
                subdomain=ConfigurationValue(
                    value="test_subdomain",
                    type="value"
                )
            ),
            blob_storage=BlobStorageConfig(
                account_url=ConfigurationValue(
                    value="test_account_url",
                    type="value"
                ),
                container_name=ConfigurationValue(
                    value="test_container_name",
                    type="value"
                )
            )
        )

        expected_env_config = EnvironmentConfig(
            key_vault_uri="https://test.vault.azure.net/",
            tenant_id="tenand_id",
            user_managed_identity=UserManagedIdentityConfig(
                client_id=ConfigurationValue(
                    value="d4fd5faf-ba63-4981-93f4-43b9314c6bd1",
                    type="value"
                )
            ),
            cosmosdb=CosmosDbConfig(
                db_name=ConfigurationValue(
                    value="test_db",
                    type="value"
                ),
                endpoint=ConfigurationValue(
                    value="https://test.endpoint.com",
                    type="value"
                ),
                configuration_collection_name=ConfigurationValue(
                    value="test_collection",
                    type="value"
                ),
                document_collection_name=ConfigurationValue(
                    value="test_collection",
                    type="value"
                )
            ),
            llm=LLMConfig(
                model_name=ConfigurationValue(
                    value="gpt-4o",
                    type="value"
                ),
                endpoint=ConfigurationValue(
                    value="https://fake.azure.openai.endpoint.com",
                    type="value"
                ),
                access_key=ConfigurationValue(
                    key="OPEN_AI_ACCESS_KEY",
                    value="test_access_key",
                    type="secret"
                ),
                api_version=ConfigurationValue(
                    value="2025-08-01-preview",
                    type="value"
                ),
                use_request_ca_bundle=ConfigurationValue(
                    value="False",
                    type="value"
                )
            ),
            default_ingest_config=DefaultIngestConfig(
                name=ConfigurationValue(
                    value="test_name",
                    type="value"
                ),
                version=ConfigurationValue(
                    value="1.0.0",
                    type="value"
                )
            ),
            content_understanding=ContentUnderstandingConfig(
                endpoint=ConfigurationValue(
                    value="https://test.endpoint.com",
                    type="value"
                ),
                subscription_key=ConfigurationValue(
                    value="test_subscription_key",
                    type="value"
                ),
                request_timeout=ConfigurationValue[int](
                    value=30,
                    type="value"
                ),
                project_id=ConfigurationValue(
                    value="test_project_id",
                    type="value"
                )
            ),
            chat_history=ChatHistoryConfig(
                endpoint=ConfigurationValue(
                    value="https://test.endpoint.com",
                    type="value"
                ),
                key=ConfigurationValue(
                    value="test_subscription_key",
                    type="value"
                ),
                db_name=ConfigurationValue(
                    value="test_db",
                    type="value"
                ),
                chat_history_container_name=ConfigurationValue(
                    value="test_collection",
                    type="value"
                ),
                user_message_limit=ConfigurationValue[int](
                    value=1,
                    type="value"
                ),
                domain=ConfigurationValue(
                    value="test_domain",
                    type="value"
                ),
                subdomain=ConfigurationValue(
                    value="test_subdomain",
                    type="value"
                )
            ),
            blob_storage=BlobStorageConfig(
                account_url=ConfigurationValue(
                    value="test_account_url",
                    type="value"
                ),
                container_name=ConfigurationValue(
                    value="test_container_name",
                    type="value"
                )
            )
        )

        mock_secret_manager = MagicMock()
        app_config_manager = AppConfigManager.AppConfigManager(
            input_env_config,
            mock_secret_manager
        )

        # act
        result = app_config_manager.hydrate_config()

        # assert
        assert result == expected_env_config
