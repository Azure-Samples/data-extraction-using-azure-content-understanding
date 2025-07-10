from pymongo import MongoClient
from pymongo.collection import Collection


class CosmosClient:
    _client: MongoClient

    def __init__(self, endpoint: str):
        """Initializes the CosmosClient with the given endpoint.

        Args:
            endpoint (str): The endpoint of the Cosmos DB.
        """
        self.client = MongoClient(endpoint)

    def get_collection(self, db_name: str, collection_name: str) -> Collection:
        """Gets the collection from the database.

        Args:
            db_name (str): The name of the database.
            collection_name (str): The name of the collection.

        Returns:
            Collection: The collection object.
        """
        db = self.client[db_name]
        db_collection = db[collection_name]

        return db_collection

    def collection_exists(self, db_name: str, collection_name: str) -> bool:
        """Checks if a collection exists in the database.

        Args:
            db_name (str): The name of the database.
            collection_name (str): The name of the collection.

        Returns:
            bool: True if the collection exists, False otherwise.
        """
        try:
            db = self.client[db_name]
            return collection_name in db.list_collection_names()
        except Exception:
            return False
