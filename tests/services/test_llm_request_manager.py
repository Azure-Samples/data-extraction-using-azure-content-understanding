import unittest
from unittest.mock import patch
from src.services.llm_request_manager import LlmRequestManager
from src.models.api.v1 import QueryResponse
from src.services.collection_kernel_plugin import CollectionPlugin
from src.models.data_collection_config import FieldDataCollectionConfig


class TestParseResponseContent(unittest.TestCase):

    def setUp(self):
        # Mock configuration for LlmRequestManager
        self.mock_config = patch('services.llm_request_manager.LlmConfig').start()
        self.mock_config.endpoint = "https://mock-endpoint.openai.azure.com"  # Provide a valid URL
        self.mock_config.key = "mock-api-key"  # Mock API key
        self.mock_config.default_model = "mock-deployment-name"  # Mock deployment name
        self.mock_config.api_version = "2023-05-15"  # Mock API version
        self.mock_config.use_request_ca_bundle = False  # Mock CA bundle usage
        self.llm_request_manager = LlmRequestManager(self.mock_config)
        config = FieldDataCollectionConfig(
            name="name",
            version="v1",
            prompt="prompt",
            lease_config_hash="hash",
            collection_rows=[])

        from src.services.collection_kernel_plugin import document_data_cache
        self.document_data_cache = document_data_cache
        self.collection_plugin = CollectionPlugin(config=config, document_service=None)
        self.collection_plugin._collection_id = "1"  # Set a mock collection ID for testing

    def tearDown(self):
        patch.stopall()

    def test_single_json_object(self):
        raw_content = '{"response": "Test response", "citations": ["CITE1-1"]}'
        key = self.collection_plugin.composite_key("1", "hash")
        self.document_data_cache[key] = {
            "citation_mappings" : {
                "CITE1-1" : {
                    "source_document": "source_document1",
                    "source_bounding_boxes" : "source_bounding_boxes1"
                }
            },
            "document_data_str": (
                "{\"id\": \"1\", \"lease_config_hash\": \"hash\", "
                "\"unstructured_data\": [{ \"key\": \"value\" }]}, "
            )
        }

        result = self.llm_request_manager._parse_response_content(raw_content, self.collection_plugin)
        expected = QueryResponse(
            response="Test response",
            citations=[["source_document1", "source_bounding_boxes1"]]
        )
        self.assertEqual(result.model_dump_json(), expected.model_dump_json())

    def test_multiple_json_objects(self):
        raw_content = (
            '{"response": "Test response 1", "citations": ["CITE1-1"]}\n'
            '{"response": "Test response 2", "citations": ["CITE1-1"]}'
        )
        key = self.collection_plugin.composite_key("1", "hash")
        self.document_data_cache[key] = {
            "citation_mappings" : {
                "CITE1-1" : {
                    "source_document": "source_document1",
                    "source_bounding_boxes" : "source_bounding_boxes1"
                }
            },
            "document_data_str": (
                "{\"id\": \"1\", \"lease_config_hash\": \"hash\", "
                "\"unstructured_data\": [{ \"key\": \"value\" }]}, "
            )
        }

        result = self.llm_request_manager._parse_response_content(raw_content, self.collection_plugin)

        expected = QueryResponse(
            response="Test response 1",
            citations=[["source_document1", "source_bounding_boxes1"]]
        )
        self.assertEqual(result.model_dump_json(), expected.model_dump_json())

    def test_pure_string_content(self):
        raw_content = "This is a pure string with no JSON object."

        key = self.collection_plugin.composite_key("1", "hash")
        self.document_data_cache[key] = {
            "citation_mappings" : {
                "CITE1-1" : {
                    "source_document": "source_document1",
                    "source_bounding_boxes" : "source_bounding_boxes1"
                }
            },
            "document_data_str": (
                "{\"id\": \"1\", \"lease_config_hash\": \"hash\", "
                "\"unstructured_data\": [{ \"key\": \"value\" }]}, "
            )
        }

        result = self.llm_request_manager._parse_response_content(raw_content, self.collection_plugin)
        expected = QueryResponse(
            response="This is a pure string with no JSON object.",
            citations=[]
        )
        self.assertEqual(result.model_dump_json(), expected.model_dump_json())

    def test_invalid_json(self):
        raw_content = '{"response": "Test response", "citations": ["doc1", "box1"]'  # Missing closing brace

        key = self.collection_plugin.composite_key("1", "hash")
        self.document_data_cache[key] = {
            "citation_mappings" : {
                "CITE1-1" : {
                    "source_document": "source_document1",
                    "source_bounding_boxes" : "source_bounding_boxes1"
                }
            },
            "document_data_str": (
                "{\"id\": \"1\", \"lease_config_hash\": \"hash\", "
                "\"unstructured_data\": [{ \"key\": \"value\" }]}, "
            )
        }

        result = self.llm_request_manager._parse_response_content(raw_content, self.collection_plugin)
        expected = QueryResponse(
            response=raw_content.strip(),
            citations=[]
        )
        self.assertEqual(result.model_dump_json(), expected.model_dump_json())
