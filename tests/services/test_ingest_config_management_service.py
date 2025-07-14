import unittest
from unittest.mock import MagicMock
from services.ingest_config_management_service import IngestConfigManagementService
from models import FieldDataCollectionConfig


class TestLoadConfig(unittest.TestCase):
    """Test the load_config method of IngestConfigManagementService."""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = IngestConfigManagementService(self.mock_db, MagicMock())

    def test_happy_path_with_config(self):
        """Test the load_config method with valid data."""
        # arrange
        name = "test_config"
        version = "1.0"
        config_data = {
            "_id": "test_config-1.0",
            "name": "test_config",
            "version": "1.0",
            "prompt": "Test prompt",
            "collection_rows": []
        }

        self.mock_db \
            .get_collection.return_value \
            .find_one.return_value = config_data

        # act
        result = self.service.load_config(f"{name}-{version}")

        # assert
        self.assertEqual(result, FieldDataCollectionConfig(**config_data))
        self.mock_db \
            .get_collection.return_value \
            .find_one.assert_called_once_with(
                {"_id": f"{name}-{version}"}
            )

    def test_happy_path_without_config(self):
        """Test the load_config method without config."""
        # arrange
        name = "test_config"
        version = "1.0"
        self.mock_db \
            .get_collection.return_value \
            .find_one.return_value = None

        # act
        result = self.service.load_config(f"{name}-{version}")

        # assert
        self.assertIsNone(result)
        self.mock_db \
            .get_collection.return_value \
            .find_one.assert_called_once_with(
                {"_id": f"{name}-{version}"}
            )


class TestUpsertConfig(unittest.TestCase):
    """Test the upsert_config method of IngestConfigManagementService."""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = IngestConfigManagementService(self.mock_db, MagicMock())

    def test_happy_path(self):
        """Test the upsert_config method with valid data."""
        # arrange
        config = FieldDataCollectionConfig(
            _id="test_config-1.0",
            name="test_config",
            version="1.0",
            prompt="Test prompt",
            collection_rows=[]
        )

        # act
        self.service.upsert_config(config)

        # assert
        self.mock_db \
            .get_collection.return_value \
            .update_one.assert_called_once_with(
                {"_id": "test_config-1.0"},
                {"$set": config.model_dump(by_alias=True)},
                upsert=True
            )
