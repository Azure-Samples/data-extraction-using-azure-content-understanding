import unittest
from unittest.mock import MagicMock
from controllers.ingest_config_controller import IngestConfigController, AnalyzerConstants
from models import FieldDataCollectionConfig, HTTPError
from models.data_collection_config import (
    LeaseAgreementCollectionRow,
    FieldSchema,
    ArrayFieldSchema,
    FieldMappingType,
    FieldMappingMethod,
    ClassifierConfig
)


class TestSetConfig(unittest.TestCase):
    """Test the set_config method of IngestConfigController."""

    def setUp(self):
        self.mock_service = MagicMock()
        self.mock_azure_content_understanding_client = MagicMock()
        self.controller = IngestConfigController(self.mock_service, self.mock_azure_content_understanding_client)

    def test_set_config_success(self):
        """Test the set_config method with valid data."""
        # arrange
        config = {
            "_id": "test_config-1.0",
            "name": "test_config",
            "version": "1.0",
            "prompt": "Test prompt",
            "collection_rows": []
        }
        name = "test_config"
        version = "1.0"
        project_id = "test_project_id"

        # act
        self.controller.set_config(config, name, version, project_id)

        # assert
        self.mock_service.upsert_config.assert_called_once_with(
            FieldDataCollectionConfig(**config)
        )

    def test_set_config_with_lease_agreement_rows(self):
        """Test the set_config method with lease agreement rows."""
        # arrange
        lease_agreement_row = LeaseAgreementCollectionRow(
            analyzer_id="test_analyzer",
            field_schema=[
                FieldSchema(name="field1", type=FieldMappingType.STRING, description="Field 1"),
                ArrayFieldSchema(
                    name="field2",
                    description="Field 2",
                    items=[
                        FieldSchema(name="item1", type=FieldMappingType.STRING, description="Item 1"),
                        FieldSchema(name="item2", type=FieldMappingType.INTEGER, description="Item 2")
                    ]
                )
            ],
            classifier=ClassifierConfig(
                enabled=False,
                classifier_id="test_classifier"
            )
        )
        config = {
            "_id": "test_config-1.0",
            "name": "test_config",
            "version": "1.0",
            "prompt": "Test prompt",
            "collection_rows": [lease_agreement_row]
        }
        name = "test_config"
        version = "1.0"
        project_id = "test_project_id"

        # Mock the methods
        self.controller._generate_lease_config_hash = MagicMock(return_value="mocked_hash")

        # act
        self.controller.set_config(config, name, version, project_id)

        # assert
        self.mock_azure_content_understanding_client.begin_create_analyzer.assert_called_once_with(
            analyzer_id="test_analyzer",
            analyzer_template={
                "scenario": AnalyzerConstants.ANALYZER_SCENARIO,
                "tags": {
                    "projectId": project_id,
                    "templateId": AnalyzerConstants.ANALYZER_TEMPLATE_ID
                },
                "fieldSchema": {
                    "fields": {
                        "field1": {
                            "name": "field1",
                            "type": FieldMappingType.STRING,
                            "description": "Field 1",
                            "method": FieldMappingMethod.EXTRACT
                        },
                        "field2": {
                            "type": "array",
                            "method": FieldMappingMethod.GENERATE,
                            "description": "Field 2",
                            "items": {
                                "type": "object",
                                "method": FieldMappingMethod.EXTRACT,
                                "properties": {
                                    "item1": {
                                        "name": "item1",
                                        "type": FieldMappingType.STRING,
                                        "description": "Item 1",
                                        "method": FieldMappingMethod.EXTRACT
                                    },
                                    "item2": {
                                        "name": "item2",
                                        "type": FieldMappingType.INTEGER,
                                        "description": "Item 2",
                                        "method": FieldMappingMethod.EXTRACT
                                    }
                                }
                            }
                        }
                    }
                }
            }
        )
        self.controller._generate_lease_config_hash.assert_called_once_with([lease_agreement_row])
        self.mock_service.upsert_config.assert_called_once()

        upserted_config = self.mock_service.upsert_config.call_args[0][0]
        self.assertEqual(upserted_config.lease_config_hash, "mocked_hash")

    def test_set_config_invalid_json(self):
        """Test the set_config method with invalid JSON data."""
        # arrange
        config = {
            "_id": "test_config-1.0",
            "name": "test_config",
            "version": "1.0",
            "collection_rows": []
        }
        name = "test_config"
        version = "1.0"
        project_id = "test_project_id"

        # act
        with self.assertRaises(HTTPError) as context:
            self.controller.set_config(config, name, version, project_id)

        # assert
        self.assertEqual(str(context.exception), "Invalid JSON data.")

    def test_set_config_name_version_mismatch(self):
        """Test the set_config method with name and version mismatch."""
        # arrange
        config = {
            "_id": "test_config-1.0",
            "name": "test_config",
            "version": "1.0",
            "prompt": "Test prompt",
            "collection_rows": []
        }
        name = "test_config"
        version = "2.0"
        project_id = "test_project_id"

        # act
        with self.assertRaises(HTTPError) as context:
            self.controller.set_config(config, name, version, project_id)

        # assert
        self.assertEqual(
            str(context.exception),
            "Configuration name and version do not match the route parameters."
        )


class TestGetConfig(unittest.TestCase):
    """Test the get_config method of IngestConfigController."""
    def setUp(self):
        self.mock_service = MagicMock()
        self.mock_azure_content_understanding_client = MagicMock()
        self.controller = IngestConfigController(self.mock_service, self.mock_azure_content_understanding_client)

    def test_get_config_success(self):
        """Test the get_config method with valid data."""
        # arrange
        config = {
            "_id": "test_config-1.0",
            "name": "test_config",
            "version": "1.0",
            "lease_config_hash": "fake-hash",
            "prompt": "Test prompt",
            "collection_rows": []
        }
        name = "test_config"
        version = "1.0"
        self.mock_service.load_config.return_value = FieldDataCollectionConfig(
            **config
        )

        # act
        response = self.controller.get_config(name, version)

        # assert
        self.assertEqual(response, config)

    def test_get_config_not_found(self):
        """Test the get_config method with config not found."""
        # arrange
        name = "test_config"
        version = "1.0"
        self.mock_service.load_config.return_value = None

        # act
        with self.assertRaises(HTTPError) as context:
            self.controller.get_config(name, version)

        # assert
        self.assertEqual(str(context.exception), "Configuration not found.")
