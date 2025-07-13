import os
import asyncio
import json
import logging
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.cosmos import CosmosClient as CosmosClient2, DatabaseProxy
from services._cosmos_client import CosmosClient
from services.secret_manager import SecretManager
from services.azure_content_understanding_client import AzureContentUnderstandingClient
from services.llm_request_manager import get_llm_request_manager
from models.environment_config import EnvironmentConfig
from utils.health_check_cache import health_check_cache, service_status


class HealthCheckController:
    """Controller to orchestrate health checks for the Function App and its dependencies."""

    def __init__(self, config: EnvironmentConfig):
        """Initialize the HealthCheckController with the application configuration.

        Args:
            config: The application configuration object.
        """
        self.config = config

    async def perform_health_checks(self):
        """Perform health checks for all critical services.

        Returns:
            dict: A dictionary containing the health status and details.
        """
        is_cached = health_check_cache.is_cache_valid()
        health_status = None

        if is_cached:
            health_status = self._get_cached_health_status()
        else:
            health_status = await self._run_health_checks()

        if health_status["status"] == "healthy":
            logging.info(json.dumps({
                "type": "health_check",
                "is_healthy": True,
                "is_cached_response": is_cached
            }))
        else:
            logging.error(json.dumps({
                "type": "health_check",
                "is_healthy": False,
                "unhealthy_services": json.dumps(health_check_cache.unhealthy_services),
                "is_cached_response": is_cached
            }))

        return health_status

    def _get_cached_health_status(self):
        """Retrieve health status from cache."""
        logging.info("Returning cached health check results.")
        health_status = {
            "status": "healthy" if health_check_cache.is_healthy else "unhealthy",
            "checks": {}
        }

        if health_check_cache.unhealthy_services:
            for service in health_check_cache.unhealthy_services:
                health_status["checks"][service["name"]] = {
                    "status": "unhealthy",
                    "details": service["message"]
                }
        else:
            for service_name in [
                "mongo_db",
                "cosmos_db",
                "key_vault",
                "content_understanding",
                "azure_openai"
            ]:
                health_status["checks"][service_name] = {
                    "status": "healthy",
                    "details": f"{service_name} is running as expected."
                }

        return health_status

    async def _run_health_checks(self):
        """Run health checks for all critical services."""
        health_status = {"status": "healthy", "checks": {}}
        checks = [
            "mongo_db",
            "cosmos_db",
            "key_vault",
            "content_understanding",
            "azure_openai"
        ]

        results = await asyncio.gather(
            self._check_mongo_db(),
            self._check_cosmos_db(),
            self._check_key_vault(),
            self._check_content_understanding(),
            self._check_azure_openai()
        )
        unhealthy_services = []
        for check, result in zip(checks, results):
            if result["status"] == "unhealthy":
                health_status["checks"][check] = result
                unhealthy_services.append({"name": check, "message": result["details"]})
            else:
                health_status["checks"][check] = result

        if unhealthy_services:
            health_check_cache.set_unhealthy_services(unhealthy_services)
            health_status["status"] = "unhealthy"
        else:
            health_check_cache.set_unhealthy_services(None)

        health_check_cache.update_time()

        if any(check["status"] == "unhealthy" for check in health_status["checks"].values()):
            health_status["status"] = "unhealthy"

        return health_status

    async def _check_mongo_db(self):
        """Check Azure Mongo DB connectivity."""
        try:
            # Mongo collections
            client = CosmosClient(self.config.cosmosdb.endpoint.value)
            database_name = self.config.cosmosdb.db_name.value

            test_collections = [self.config.cosmosdb.configuration_collection_name.value,
                                self.config.cosmosdb.document_collection_name.value]

            for collection_name in test_collections:
                if not client.collection_exists(database_name, collection_name):
                    raise ValueError(f"Collection '{collection_name}' does not exist in database '{database_name}'.")

            logging.info("All required Mongo DB Collections exist.")

            return {
                "status": "healthy",
                "details": "mongo_db is running as expected."
            }
        except Exception as e:
            logging.error(f"mongo_db check failed with error: {str(e)}")
            return {
                "status": "unhealthy",
                "details": str(e)
            }

    async def _check_cosmos_db(self):
        """Check Azure Cosmos DB connectivity."""
        try:
            # Cosmos container
            credentials = None
            if os.environ.get("ENVIRONMENT") == "local" and self.config.user_managed_identity.client_id:
                credentials = DefaultAzureCredential()
            elif self.config.user_managed_identity.client_id:
                credentials = ManagedIdentityCredential(
                    client_id=self.config.user_managed_identity.client_id.value
                )
            else:
                credentials = DefaultAzureCredential()

            client = CosmosClient2(self.config.chat_history.endpoint.value, credential=credentials)

            databases = list(client.list_databases())
            database_name = self.config.chat_history.db_name.value

            if not any(db['id'] == database_name for db in databases):
                raise ValueError(f"Database '{database_name}' does not exist.")

            database_proxy: DatabaseProxy = client.get_database_client(database_name)
            containers = list(database_proxy.list_containers())

            container_name = self.config.chat_history.chat_history_container_name.value
            if not any(container["id"] == container_name for container in containers):
                raise ValueError(f"Container '{container_name}' does not exist in the database '{database_name}'.")

            logging.info(f"Database '{database_name}' and container {container_name} is accessible.")
            return {
                "status": "healthy",
                "details": (
                    "cosmos_db is running as expected."
                )
            }
        except Exception as e:
            logging.error(f"cosmos_db check failed with error: {str(e)}")
            return {
                "status": "unhealthy",
                "details": str(e)
            }

    async def _check_key_vault(self):
        """Check Azure Key Vault accessibility."""
        try:
            credentials = None
            if self.config.user_managed_identity.client_id:
                credentials = ManagedIdentityCredential(
                    client_id=self.config.user_managed_identity.client_id.value
                )
            else:
                credentials = DefaultAzureCredential()

            client = SecretManager.from_url(
                self.config.key_vault_uri,
                credentials
            )

            secrets = list(client.list_secrets())
            logging.info(f"Key Vault retrieved {len(secrets)} secrets.")
            return {"status": "healthy", "details": "key_vault is running as expected."}
        except Exception as e:
            logging.error(f"key_vault check failed with error: {str(e)}")
            return {
                "status": "unhealthy",
                "details": str(e)
            }

    async def _check_content_understanding(self):
        """Check Content Understanding service status."""
        try:
            client = AzureContentUnderstandingClient(
                endpoint=self.config.content_understanding.endpoint.value,
                subscription_key=self.config.content_understanding.subscription_key.value
            )
            analyzers = client.get_all_analyzers()
            logging.info(f"Content Understanding service is responsive. "
                         f"Found {len(analyzers)} analyzers.")
            return {
                "status": "healthy",
                "details": (
                    "content_understanding is running as expected."
                )
            }
        except Exception as e:
            logging.error(f"content_understanding check failed with error: {str(e)}")
            return {
                "status": "unhealthy",
                "details": str(e)
            }

    async def _check_azure_openai(self):
        """Check Azure OpenAI connectivity."""
        try:
            if service_status["openai"] is None or service_status["openai"]["status"] != "healthy" :
                llm_manager = get_llm_request_manager()
                system_message = "System Test"
                user_message = "Ping"
                response = await llm_manager.answer_general_question(system_message, user_message)
                logging.info(f"Connected to Azure OpenAI deployment. Answered: '{response}'")

                service_status["openai"] = {"status": "healthy", "details": "azure_openai is running as expected."}
        except Exception as e:
            logging.error(f"azure_openai check failed with error: {str(e)}")

            service_status["openai"] = {
                "status": "unhealthy",
                "details": str(e)
            }

        return service_status["openai"]
