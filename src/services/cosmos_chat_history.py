import logging
from enum import Enum

from pydantic import Field
from typing import Any
from semantic_kernel.kernel_pydantic import KernelBaseModel

from semantic_kernel.contents import (
    ChatHistory
)
from semantic_kernel.contents.chat_message_content import ChatMessageContent, AuthorRole
from semantic_kernel.contents.history_reducer.chat_history_reducer_utils import contains_function_call_or_result
from semantic_kernel.exceptions import ContentInitializationError
from azure.core.credentials import TokenCredential
from azure.identity import ManagedIdentityCredential, DefaultAzureCredential
from azure.cosmos import CosmosClient, DatabaseProxy, ContainerProxy, CosmosDict
from azure.cosmos.exceptions import CosmosHttpResponseError
from models.environment_config import EnvironmentConfig
from models.api.v1 import QueryResponse
from utils.citation_cleaner import remove_inline_citations_preserve_spacing


class ChatMessageType(str, Enum):
    INTERNAL = "internal"
    AI = "ai"
    HUMAN = "human"


class ChatMessageData(KernelBaseModel):
    content: str


class ChatMessageWithTypeAndData(ChatMessageContent):
    type: ChatMessageType
    data: ChatMessageData


class ChatHistoryModel(KernelBaseModel, extra="ignore"):
    id: str
    user_id: str
    messages: list[ChatMessageWithTypeAndData]
    domain: str
    subdomain: str


class CosmosChatHistory(ChatHistory):
    container: ContainerProxy
    user_message_limit: int
    domain: str
    subdomain: str
    remove_tool_calls: bool = False
    internal_messages: list[ChatMessageContent] = Field(default_factory=list, kw_only=False)

    def _message_to_type(self, msg: ChatMessageContent) -> ChatMessageType:
        """Convert the message to a type.

        Args:
            msg (ChatMessageContent): The message content.

        Returns:
            ChatMessageType: The message type.
        """
        if contains_function_call_or_result(msg):
            return ChatMessageType.INTERNAL
        if msg.role == AuthorRole.USER:
            return ChatMessageType.HUMAN
        if msg.role == AuthorRole.ASSISTANT:
            return ChatMessageType.AI
        return ChatMessageType.INTERNAL

    def add_message(
        self,
        message: ChatMessageContent | dict[str, Any],
        encoding: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a message to the history.

        This method accepts either a ChatMessageContent instance or a
        dictionary with the necessary information to construct a ChatMessageContent instance.

        Args:
            message (Union[ChatMessageContent, dict]): The message to add, either as
                a pre-constructed ChatMessageContent instance or a dictionary specifying 'role' and 'content'.
            encoding (Optional[str]): The encoding of the message. Required if 'message' is a dict.
            metadata (Optional[dict[str, Any]]): Any metadata to attach to the message. Required if 'message' is a dict.
        """
        if isinstance(message, ChatMessageContent):
            self.internal_messages.append(message)
            self.messages.append(message)
            return
        if "role" not in message:
            raise ContentInitializationError(f"Dictionary must contain at least the role. Got: {message}")
        if encoding:
            message["encoding"] = encoding
        if metadata:
            message["metadata"] = metadata
        self.internal_messages.append(ChatMessageContent(**message))
        self.messages.append(ChatMessageContent(**message))

    def store_messages(
        self,
        session_id: str,
        user_id: str,
    ) -> None:
        """Store the chat history in the Cosmos DB.

        Args:
            session_id (str): The session ID.
            user_id (str): The user ID.
        """
        messages = []
        for message in self.internal_messages:
            message_type = self._message_to_type(message)
            content = message.content
            messages.append(ChatMessageWithTypeAndData(
                **message.model_dump(),
                type=message_type,
                data=ChatMessageData(content=content),
            ).model_dump())

        chat_history_message = ChatHistoryModel(
            id=session_id,
            user_id=user_id.lower(),
            messages=messages,
            domain=self.domain,
            subdomain=self.subdomain,
        )
        self.container.upsert_item(
            body=chat_history_message.model_dump()
        )

    def read_messages(
        self,
        session_id: str,
        user_id: str,
    ) -> None:
        """Read the chat history from the Cosmos DB.

        Note that we use the model_validate method to convert the serializable format back into a ChatMessageContent.
        """
        doc: CosmosDict
        try:
            doc = self.container.read_item(
                item=session_id, partition_key=[user_id.lower(), self.domain, self.subdomain]
            )
        except CosmosHttpResponseError:
            logging.info("no session found")
            return

        chat_history_model = ChatHistoryModel(**doc)
        self.internal_messages = [
            ChatMessageContent(**message.model_dump()) for message in chat_history_model.messages
        ]
        self.messages = []

        for internal_message in self.internal_messages:
            # Mark when we find a tool call (function call or result)
            if self.remove_tool_calls and contains_function_call_or_result(internal_message):
                continue

            message = internal_message.model_copy(deep=True)
            if message.role == AuthorRole.ASSISTANT and message.content.startswith("{"):
                content = message.content
                try:
                    content = QueryResponse.model_validate_json(content)
                    content = remove_inline_citations_preserve_spacing(content.response)
                except Exception:
                    logging.warning(
                        "Failed to parse message content as QueryResponse: %s", content
                    )
                message.content = content
            self.messages.append(message)

    @property
    def user_message_limit_exceeded(self) -> bool:
        """Check if the user message limit has been hit.

        Returns:
            bool: True if the user message limit has been hit, False otherwise.
        """
        user_messages = [
            message for message in self.internal_messages if message.role == AuthorRole.USER
        ]
        return len(user_messages) >= self.user_message_limit


_cosmos_container: ContainerProxy | None = None


def get_cosmos_chat_history(env_name, environment_config: EnvironmentConfig) -> CosmosChatHistory:
    """Get the CosmosChatHistory instance.

    Returns:
        CosmosChatHistory: The CosmosChatHistory instance.
    """
    global _cosmos_container
    if _cosmos_container is None:
        credential: TokenCredential | str | None = None
        if key := environment_config.chat_history.key:
            credential = key.value
        if env_name == "local" and environment_config.user_managed_identity.client_id:
            credential = DefaultAzureCredential()
        elif client_id := environment_config.user_managed_identity.client_id:
            credential = ManagedIdentityCredential(
                client_id=client_id.value
            )
        else:
            credential = DefaultAzureCredential()
        cosmos_client = CosmosClient(
            url=environment_config.chat_history.endpoint.value,
            credential=credential,
        )
        database_client: DatabaseProxy = cosmos_client.get_database_client(
            environment_config.chat_history.db_name.value
        )
        container_client: ContainerProxy = database_client.get_container_client(
            environment_config.chat_history.chat_history_container_name.value
        )
        _cosmos_container = container_client
    chat_history = CosmosChatHistory(
        container=_cosmos_container,
        user_message_limit=environment_config.chat_history.user_message_limit.value,
        domain=environment_config.chat_history.domain.value,
        subdomain=environment_config.chat_history.subdomain.value,
        remove_tool_calls=True if environment_config.chat_history.remove_tool_calls.value.lower() == "true" else False,
    )

    return chat_history
