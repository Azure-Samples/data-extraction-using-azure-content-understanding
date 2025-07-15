import unittest
from unittest.mock import MagicMock
from controllers.inference_controller import InferenceController
from services.ingest_config_management_service import IngestConfigManagementService
from services.ingest_lease_documents_service import IngestionCollectionDocumentService
from services.llm_request_manager import LlmRequestManager
from models.api.v1 import QueryRequest, QueryResponse, QueryMetrics
from services.cosmos_chat_history import CosmosChatHistory
from models import HTTPError
import asyncio


class TestInferenceController(unittest.TestCase):

    def setUp(self):
        self.llm_request_manager = MagicMock(spec=LlmRequestManager)
        self.config_management_service = MagicMock(spec=IngestConfigManagementService)
        self.chat_history = MagicMock(spec=CosmosChatHistory)
        self.lease_docs_service = MagicMock(spec=IngestionCollectionDocumentService)
        self.controller = InferenceController(
            self.llm_request_manager,
            self.config_management_service,
            self.chat_history,
            self.lease_docs_service
        )

        self.invalid_citation_placeholder = ["Invalid citation", ""]

    def test_query_config_not_found(self):
        request = QueryRequest(query="test query", sid="1234", cid="test-correlation-id")
        config_name = "test_config"
        config_version = "1.0"
        user_id = "user123"

        self.config_management_service.load_config.return_value = None

        with self.assertRaises(HTTPError) as context:
            asyncio.run(self.controller.query(request, config_name, config_version, user_id))

        self.assertEqual(str(context.exception), "Configuration not found.")
        self.assertEqual(context.exception.status_code, 404)

    def test_query_user_message_limit_exceeded(self):
        request = QueryRequest(query="test query", sid="1234", cid="test-correlation-id")
        config_name = "test_config"
        config_version = "1.0"
        user_id = "user123"
        config = MagicMock()
        config.prompt = "test prompt"
        self.config_management_service.load_config.return_value = config
        self.chat_history.user_message_limit_exceeded = True

        with self.assertRaises(HTTPError) as context:
            asyncio.run(self.controller.query(request, config_name, config_version, user_id))

        self.assertEqual(str(context.exception), "User message limit exceeded.")
        self.assertEqual(context.exception.status_code, 400)

    def test_query_success(self):
        request = QueryRequest(query="test query", sid="1234", cid="test-correlation-id")
        config_name = "test_config"
        config_version = "1.0"
        user_id = "user123"
        config = MagicMock()
        config.prompt = "test prompt"
        self.config_management_service.load_config.return_value = config
        test_response = "test response"
        test_citations = [["test_doc", "test_bounding_boxes"]]
        test_metrics = QueryMetrics(prompt_tokens=100,
                                    completion_tokens=10,
                                    total_tokens=110,
                                    total_latency_sec=20.0)
        self.llm_request_manager.answer_collection_question.return_value = QueryResponse(
            response=test_response, citations=test_citations, metrics=test_metrics).model_dump_json()
        self.chat_history.user_message_limit_exceeded = False
        self.chat_history.messages = []

        # Mock the tool_call_output for citation validation
        tool_call_output = ('"...test_field": {"document_type": "LeaseAgreement", "value": "test","'
                            '"source_document": "test_doc", "source_bounding_boxes": "test_bounding_boxes"}')
        self.controller._get_latest_collection_plugin_output = MagicMock(return_value=tool_call_output)

        response = asyncio.run(self.controller.query(request, config_name, config_version, user_id))

        self.config_management_service.load_config.assert_called_once_with(f"{config_name}-{config_version}")
        self.llm_request_manager.answer_collection_question.assert_called_once_with(
            config.prompt,
            request.query,
            unittest.mock.ANY,
            self.chat_history
        )
        # Instead of checking the instance type directly, check the class name
        self.assertEqual(response.__class__.__name__, "QueryResponse")
        self.assertEqual(response.response, test_response)
        self.assertEqual(response.citations, test_citations)
