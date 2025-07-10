import logging

from pydantic import ValidationError

from services.ingest_config_management_service import IngestConfigManagementService
from services.ingest_lease_documents_service import IngestionSiteLeaseService
from services.llm_request_manager import LlmRequestManager
from services.site_kernel_plugin import SitePlugin
from services.cosmos_chat_history import CosmosChatHistory
from utils.document_utils import build_config_id
from models import HTTPError
from models.api.v1 import QueryRequest, QueryResponse


class InferenceController(object):
    _llm_request_manager: LlmRequestManager
    _config_management_service: IngestConfigManagementService
    _chat_history: CosmosChatHistory
    _lease_documents_service: IngestionSiteLeaseService

    def __init__(
        self,
        llm_request_manager: LlmRequestManager,
        config_management_service: IngestConfigManagementService,
        chat_history: CosmosChatHistory,
        lease_documents_service: IngestionSiteLeaseService
    ):
        """Initializes the Inference Controller.

        Args:
            llm_request_manager (LlmRequestManager): The LLM request manager.
            config_management_service (IngestConfigManagementService):
                The ConfigManagementService instance.
            chat_history (CosmosChatHistory): The chat history service.
            lease_documents_service (IngestionSiteLeaseService):
                The service to manage lease documents ingested using Content Understanding.
        """
        self._llm_request_manager = llm_request_manager
        self._config_management_service = config_management_service
        self._chat_history = chat_history
        self._lease_documents_service = lease_documents_service

    async def query(
        self,
        query_request: QueryRequest,
        config_name: str,
        config_version: str,
        user_id: str
    ) -> QueryResponse:
        """Handles the query request.

        Args:
            request (dict): The query request data.
            config_name (str): The configuration name.
            config_version (str): The configuration version.
            user_id (str): The user ID.

        Returns:
            QueryResponse: The query response.
        """
        logging.info(f"Querying with config: {config_name}; version: {config_version}")
        config_id = build_config_id(config_name, config_version)
        config = self._config_management_service.load_config(config_id)

        if not config:
            raise HTTPError("Configuration not found.", 404)

        site_plugin = SitePlugin(config, self._lease_documents_service)
        self._chat_history.read_messages(query_request.sid, user_id)
        if self._chat_history.user_message_limit_exceeded:
            raise HTTPError("User message limit exceeded.", 400)

        result = await self._llm_request_manager.answer_site_question(
            config.prompt,
            query_request.query,
            site_plugin,
            self._chat_history,
        )
        self._chat_history.store_messages(query_request.sid, user_id)

        try:
            output = QueryResponse.model_validate_json(result)
        except ValidationError:
            raise HTTPError(f"Invalid JSON for QueryResponse: {result}", 500)

        return output
