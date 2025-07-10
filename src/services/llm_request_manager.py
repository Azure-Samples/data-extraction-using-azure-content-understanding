import logging

import httpx
import ssl
import os
import time
from openai import AsyncAzureOpenAI
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.contents import ChatHistory
from services.site_kernel_plugin import SitePlugin
from configs.llm_config import LlmConfig, get_llm_config
from models.api.v1 import QueryResponse, GeneratedResponse, QueryMetrics
import re
import json
from services.citation_mapper import CitationMapper
from utils.health_check_cache import service_status


class LlmRequestManager:
    _chat_completions: AzureChatCompletion | OpenAIChatCompletion
    _config: LlmConfig

    def __init__(self, config: LlmConfig):
        """LLM Request manager constructor."""
        config = config

        http_client = httpx.AsyncClient()

        async_openai_client = AsyncAzureOpenAI(
            http_client=http_client,
            api_key=config.key,
            base_url=config.endpoint,
            api_version=config.api_version,
            azure_deployment=config.default_model
        )

        self._chat_completions = AzureChatCompletion(
            service_id="inference-service",
            api_key=config.key,
            base_url=config.endpoint,
            api_version=config.api_version,
            deployment_name=config.default_model,
            async_client=async_openai_client
        )
        self._citation_mapper = CitationMapper()

    def _parse_response_content(self,
                                raw_content: str,
                                site_plugin: SitePlugin) -> QueryResponse:
        """Parses the raw content to extract the first valid JSON object or handle plain strings."""
        try:
            # Use a regex to extract all valid JSON objects from the response
            json_objects = re.findall(r'\{.*?\}', raw_content, re.DOTALL)

            if json_objects:
                if len(json_objects) > 1:
                    logging.warning("More than one JSON object found in the response. Using the first one.")

                # Parse the first valid JSON object
                first_payload = json.loads(json_objects[0])
                response = first_payload.get("response", "")
                citations = first_payload.get("citations", [])
            else:
                # If no JSON objects are found, treat the content as a plain string
                logging.warning("The raw content is a pure string with no JSON object.")
                response = raw_content.strip()
                citations = []
        except (json.JSONDecodeError, ValueError) as e:
            logging.error(f"Error parsing response: {e}")
            response = raw_content.strip()  # Fallback to raw content
            citations = []

        # structured_data = site_plugin.restore_structured_data()
        citations = site_plugin.restore_citations(citations)
        query_response = QueryResponse(
            response=response,
            citations=citations,
            metadata={
                # "structured_data": structured_data,
                "unstructured_data": []
            }
        )
        return query_response

    async def answer_site_question(
        self,
        system_message: str,
        user_message: str,
        site_plugin: SitePlugin,
        history: ChatHistory
    ) -> str:
        kernel = Kernel()

        site_plugin_name = "Site"
        kernel.add_service(self._chat_completions)
        kernel.add_plugin(
            site_plugin,
            plugin_name=site_plugin_name,
        )

        execution_settings = AzureChatPromptExecutionSettings()
        execution_settings.function_choice_behavior = FunctionChoiceBehavior.Required(
            included_functions=[
                f"{site_plugin_name}-{SitePlugin.get_site_data.__kernel_function_name__}"
            ]
        )
        execution_settings.response_format = GeneratedResponse

        if len(history.messages or []) == 0:
            history.add_system_message(system_message)
        history.add_user_message(user_message)

        logging.info(f"Running query '{user_message}'")
        start_time = time.perf_counter()
        result = None
        try:
            result = await self._chat_completions.get_chat_message_content(
                chat_history=history,
                settings=execution_settings,
                kernel=kernel
            )
            service_status["openai"] = {"status": "healthy", "details": "azure_openai is running as expected."}
        except Exception as e:
            logging.error(f"azure_openai check failed with error: {str(e)}")

            service_status["openai"] = {
                "status": "unhealthy",
                "details": str(e)
            }
            raise e

        end_time = time.perf_counter()
        latency = end_time - start_time

        # tokens = result.inner_content.usage.prompt_tokens, total_tokens, completion_tokens
        query_metrics = QueryMetrics(prompt_tokens=result.inner_content.usage.prompt_tokens,
                                     completion_tokens=result.inner_content.usage.completion_tokens,
                                     total_tokens=result.inner_content.usage.total_tokens,
                                     total_latency_sec=latency)

        # Parse the raw content and handle invalid json content, then add to chat history
        query_response = self._parse_response_content(result.content, site_plugin)
        history.add_assistant_message(query_response.model_dump_json())

        # Add metrics to the response after it's been recorded in the chat history
        query_response.metrics = query_metrics
        return query_response.model_dump_json()

    async def answer_general_question(self, system_message: str, user_message: str) -> str:
        kernel = Kernel()

        kernel.add_service(self._chat_completions)

        execution_settings = AzureChatPromptExecutionSettings()
        execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
        execution_settings.parallel_tool_calls = False

        history = ChatHistory()
        history.add_system_message(system_message)
        history.add_user_message(user_message)

        logging.info(f"Running query '{user_message}'")
        result = await self._chat_completions.get_chat_message_content(
            chat_history=history,
            settings=execution_settings,
            kernel=kernel
        )
        return result.content


llm_request_manager: LlmRequestManager | None = None


def get_llm_request_manager() -> LlmRequestManager:
    """Gets the LLM Request Manager as singleton."""
    global llm_request_manager
    if not llm_request_manager:
        llm_request_manager = LlmRequestManager(get_llm_config())
    return llm_request_manager
