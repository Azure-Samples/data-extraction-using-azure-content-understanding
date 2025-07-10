from pymongo.collection import Collection
from ._cosmos_client import CosmosClient
from models import FieldDataCollectionConfig
from models.environment_config import EnvironmentConfig


class IngestConfigManagementService(object):
    _collection: Collection

    def __init__(self, cosmos_client: CosmosClient, environment_config: EnvironmentConfig):
        """Initializes the ConfigManagementService with the given CosmosClient.

        Args:
            cosmos_client (CosmosClient): The CosmosClient instance.
            environment_config (EnvironmentConfig): The environment configuration.
        """
        self._collection = cosmos_client.get_collection(
            environment_config.cosmosdb.db_name.value,
            environment_config.cosmosdb.configuration_collection_name.value
        )

    def load_config(
        self,
        id: str
    ) -> FieldDataCollectionConfig | None:
        """Loads the configuration from the database.

        Args:
            id (str): The ID of the configuration.

        Returns:
            dict: The configuration data.
        """
        config = self._collection.find_one({"_id": id})

        if config:
            return FieldDataCollectionConfig(**config)
        return None

    def upsert_config(self, config: FieldDataCollectionConfig):
        """Upserts the configuration in the database.

        Args:
            config (dict): The configuration data.
        """
        self._collection.update_one(
            {"_id": config.id},
            {"$set": config.model_dump(by_alias=True)},
            upsert=True
        )

    @classmethod
    def from_environment_config(cls, environment_config: EnvironmentConfig):
        """Creates a ConfigManagementService instance from a connection string.

        Args:
            environment_config (EnvironmentConfig): The environment configuration.

        Returns:
            ConfigManagementService: The ConfigManagementService instance.
        """
        cosmos_client = CosmosClient(environment_config.cosmosdb.endpoint.value)
        return cls(cosmos_client, environment_config)
