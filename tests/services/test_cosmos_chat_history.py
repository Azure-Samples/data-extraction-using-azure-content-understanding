import unittest
from unittest.mock import Mock, patch
import json
from azure.cosmos.exceptions import CosmosHttpResponseError
from azure.cosmos import ContainerProxy
from semantic_kernel.contents import ChatMessageContent, AuthorRole, FunctionCallContent, FunctionResultContent
from semantic_kernel.exceptions import ContentInitializationError
from semantic_kernel.contents import TextContent
from semantic_kernel.contents.const import ContentTypes
from models.api.v1 import QueryResponse, QueryMetrics
from services.cosmos_chat_history import (
    CosmosChatHistory,
    ChatMessageWithTypeAndData,
    ChatMessageData,
    ChatMessageType
)


class TestCosmosChatHistoryStoreMessages(unittest.TestCase):
    def setUp(self):
        self.mock_container = Mock(spec=ContainerProxy)
        self.domain = "test_domain"
        self.subdomain = "test_subdomain"
        self.chat_history = CosmosChatHistory(
            container=self.mock_container,
            user_message_limit=20,
            domain=self.domain,
            subdomain=self.subdomain
        )
        self.chat_history.internal_messages = [
            ChatMessageContent(role=AuthorRole.USER, content="Hello"),
            ChatMessageContent(role=AuthorRole.ASSISTANT, content="", items=[
                FunctionCallContent(id="call1", content="Tool call")
            ]),
            ChatMessageContent(role=AuthorRole.TOOL, content="", items=[
                FunctionResultContent(id="call1", content="Tool response")
            ]),
            ChatMessageContent(role=AuthorRole.ASSISTANT, content="Hi, how can I help?")
        ]

    def test_store_messages_success(self):
        # arrange
        session_id = "session123"
        user_id = "user456"

        # act
        self.chat_history.store_messages(session_id, user_id)

        # assert
        self.mock_container.upsert_item.assert_called_once()
        _, kwargs = self.mock_container.upsert_item.call_args
        body = kwargs["body"]

        expected_messages = [
            ChatMessageWithTypeAndData(
                **self.chat_history.internal_messages[0].model_dump(),
                type=ChatMessageType.HUMAN,
                data=ChatMessageData(content="Hello")
            ).model_dump(),
            ChatMessageWithTypeAndData(
                **self.chat_history.internal_messages[1].model_dump(),
                type=ChatMessageType.INTERNAL,
                data=ChatMessageData(content="")
            ).model_dump(),
            ChatMessageWithTypeAndData(
                **self.chat_history.internal_messages[2].model_dump(),
                type=ChatMessageType.INTERNAL,
                data=ChatMessageData(content="")
            ).model_dump(),
            ChatMessageWithTypeAndData(
                **self.chat_history.internal_messages[3].model_dump(),
                type=ChatMessageType.AI,
                data=ChatMessageData(content="Hi, how can I help?")
            ).model_dump()
        ]

        self.assertEqual(body["id"], session_id)
        self.assertEqual(body["user_id"], user_id)
        self.assertEqual(body["messages"], expected_messages)
        self.assertEqual(body["domain"], self.domain)
        self.assertEqual(body["subdomain"], self.subdomain)


class TestCosmosChatHistoryReadMessages(unittest.TestCase):
    def setUp(self):
        self.mock_container = Mock(spec=ContainerProxy)
        self.domain = "test_domain"
        self.subdomain = "test_subdomain"
        self.chat_history = CosmosChatHistory(
            container=self.mock_container,
            user_message_limit=20,
            domain=self.domain,
            subdomain=self.subdomain
        )

    def test_read_message_query_result_success(self):
        session_id = "session123"
        user_id = "user456"
        query_result = QueryResponse(
            response="Some response with a citation[1].",
            citations=[
                [
                    "/some/path/1",
                    "d(1, 1, 1, 1, 1);"
                ]
            ],
            metrics=QueryMetrics(prompt_tokens=100,
                                 completion_tokens=10,
                                 total_tokens=110,
                                 total_latency_sec=20.0)
        ).model_dump_json()
        mock_doc = {
            "id": session_id,
            "user_id": user_id,
            "domain": self.domain,
            "subdomain": self.subdomain,
            "messages": [
                {
                    "role": "user",
                    "content": "Hello",
                    "type": "human",
                    "data": {"content": "Hello"}
                },
                {
                    "role": "assistant",
                    "content": query_result,
                    "type": "ai",
                    "data": {"content": query_result}
                }
            ]
        }

        self.mock_container.read_item.return_value = mock_doc

        self.chat_history.read_messages(session_id, user_id)

        self.mock_container.read_item.assert_called_once_with(
            item=session_id,
            partition_key=[user_id, self.domain, self.subdomain]
        )

        expected_messages = [
            ChatMessageContent(role=AuthorRole.USER, content="Hello"),
            ChatMessageContent(role=AuthorRole.ASSISTANT, content="Some response with a citation.")
        ]
        expected_internal_messages = [
            ChatMessageContent(role=AuthorRole.USER, content="Hello"),
            ChatMessageContent(role=AuthorRole.ASSISTANT, content=query_result)
        ]

        self.assertEqual(self.chat_history.messages, expected_messages)
        self.assertEqual(self.chat_history.internal_messages, expected_internal_messages)

    def test_read_message_object_not_query_response_returns_object(self):
        session_id = "session123"
        user_id = "user456"
        query_result = {
            "key1": "value1",
            "key2": "value2"
        }
        query_result = json.dumps(query_result)
        mock_doc = {
            "id": session_id,
            "user_id": user_id,
            "domain": self.domain,
            "subdomain": self.subdomain,
            "messages": [
                {
                    "role": "user",
                    "content": "Hello",
                    "type": "human",
                    "data": {"content": "Hello"}
                },
                {
                    "role": "assistant",
                    "content": query_result,
                    "type": "ai",
                    "data": {"content": query_result}
                }
            ]
        }

        self.mock_container.read_item.return_value = mock_doc

        self.chat_history.read_messages(session_id, user_id)

        self.mock_container.read_item.assert_called_once_with(
            item=session_id,
            partition_key=[user_id, self.domain, self.subdomain]
        )

        expected_messages = [
            ChatMessageContent(role=AuthorRole.USER, content="Hello"),
            ChatMessageContent(role=AuthorRole.ASSISTANT, content=query_result)
        ]
        expected_internal_messages = [
            ChatMessageContent(role=AuthorRole.USER, content="Hello"),
            ChatMessageContent(role=AuthorRole.ASSISTANT, content=query_result)
        ]

        self.assertEqual(self.chat_history.messages, expected_messages)
        self.assertEqual(self.chat_history.internal_messages, expected_internal_messages)

    def test_read_messages_success(self):
        session_id = "session123"
        user_id = "user456"
        mock_doc = {
            "id": session_id,
            "user_id": user_id,
            "domain": self.domain,
            "subdomain": self.subdomain,
            "messages": [
                {
                    "role": "user",
                    "content": "Hello",
                    "type": "human",
                    "data": {"content": "Hello"}
                },
                {
                    "role": "assistant",
                    "content": "Hi, how can I help?",
                    "type": "ai",
                    "data": {"content": "Hi, how can I help?"}
                }
            ]
        }

        self.mock_container.read_item.return_value = mock_doc

        self.chat_history.read_messages(session_id, user_id)

        self.mock_container.read_item.assert_called_once_with(
            item=session_id,
            partition_key=[user_id, self.domain, self.subdomain]
        )

        expected_messages = [
            ChatMessageContent(role=AuthorRole.USER, content="Hello"),
            ChatMessageContent(role=AuthorRole.ASSISTANT, content="Hi, how can I help?")
        ]

        self.assertEqual(self.chat_history.messages, expected_messages)
        self.assertEqual(self.chat_history.internal_messages, expected_messages)

    def test_read_messages_no_messages(self):
        session_id = "session123"
        user_id = "user456"
        mock_doc = {
            "id": session_id,
            "user_id": user_id,
            "domain": self.domain,
            "subdomain": self.subdomain,
            "messages": []
        }
        self.mock_container.read_item.return_value = mock_doc
        self.chat_history.read_messages(session_id, user_id)

        self.mock_container.read_item.assert_called_once_with(
            item=session_id,
            partition_key=[user_id, self.domain, self.subdomain]
        )

        self.assertEqual(self.chat_history.messages, [])
        self.assertEqual(self.chat_history.internal_messages, [])

    def test_read_messages_with_tool_call_when_remove_tool_calls_prunes_messages(self):
        session_id = "session123"
        user_id = "user456"
        mock_doc = {
            "id": session_id,
            "user_id": user_id,
            "domain": self.domain,
            "subdomain": self.subdomain,
            "messages": [
                {
                    "role": "system",
                    "content": "System message",
                    "type": "internal",
                    "data": {"content": "System message"}
                },
                {
                    "role": "user",
                    "content": "Hello",
                    "type": "human",
                    "data": {"content": "Hello"}
                },
                {
                    "role": "assistant",
                    "content": "",
                    "type": "ai",
                    "data": {"content": ""}
                },
                {
                    "role": "user",
                    "content": "test",
                    "type": "human",
                    "data": {"content": "test"}
                },
                {
                    "role": "tool",
                    "items": [
                        {
                            "metadata": {},
                            "content_type": "function_result",
                            "id": "test",
                            "result": "test",
                            "name": "test",
                            "function_name": "test_fn",
                            "plugin_name": "Function",
                        }
                    ],
                    "type": "internal",
                    "data": {
                        "content": ""
                    }
                },
                {
                    "role": "assistant",
                    "content": "Hi, how can I help?",
                    "type": "ai",
                    "data": {"content": ""}
                }
            ]
        }

        self.mock_container.read_item.return_value = mock_doc
        self.chat_history.remove_tool_calls = True
        self.chat_history.read_messages(session_id, user_id)
        self.mock_container.read_item.assert_called_once_with(
            item=session_id,
            partition_key=[user_id, self.domain, self.subdomain]
        )
        expected_internal_messages = [
            ChatMessageContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type=ContentTypes.CHAT_MESSAGE_CONTENT,
                role=AuthorRole.SYSTEM,
                name=None,
                items=[
                    TextContent(
                        inner_content=None,
                        ai_model_id=None,
                        metadata={},
                        content_type=ContentTypes.TEXT_CONTENT,
                        text='System message',
                        encoding=None
                    )
                ],
                encoding=None,
                finish_reason=None
            ),
            ChatMessageContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type=ContentTypes.CHAT_MESSAGE_CONTENT,
                role=AuthorRole.USER,
                name=None,
                items=[
                    TextContent(
                        inner_content=None,
                        ai_model_id=None,
                        metadata={},
                        content_type=ContentTypes.TEXT_CONTENT,
                        text='Hello',
                        encoding=None
                    )
                ],
                encoding=None,
                finish_reason=None
            ),
            ChatMessageContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type=ContentTypes.CHAT_MESSAGE_CONTENT,
                role=AuthorRole.ASSISTANT,
                name=None,
                items=[],
                encoding=None,
                finish_reason=None
            ),
            ChatMessageContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type=ContentTypes.CHAT_MESSAGE_CONTENT,
                role=AuthorRole.USER,
                name=None,
                items=[
                    TextContent(
                        inner_content=None,
                        ai_model_id=None,
                        metadata={},
                        content_type=ContentTypes.TEXT_CONTENT,
                        text='test',
                        encoding=None
                    )
                ],
                encoding=None,
                finish_reason=None
            ),
            ChatMessageContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type=ContentTypes.CHAT_MESSAGE_CONTENT,
                role=AuthorRole.TOOL,
                name=None,
                items=[
                    FunctionResultContent(
                        inner_content=None,
                        ai_model_id=None,
                        metadata={},
                        content_type=ContentTypes.FUNCTION_RESULT_CONTENT,
                        id='test',
                        result='test',
                        name='test',
                        function_name='test_fn',
                        plugin_name='Function',
                        encoding=None
                    )
                ],
                encoding=None,
                finish_reason=None
            ),
            ChatMessageContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type=ContentTypes.CHAT_MESSAGE_CONTENT,
                role=AuthorRole.ASSISTANT,
                name=None,
                items=[
                    TextContent(
                        inner_content=None,
                        ai_model_id=None,
                        metadata={},
                        content_type=ContentTypes.TEXT_CONTENT,
                        text='Hi, how can I help?',
                        encoding=None
                    )
                ],
                encoding=None,
                finish_reason=None
            )
        ]
        expected_messages = [
            ChatMessageContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type=ContentTypes.CHAT_MESSAGE_CONTENT,
                role=AuthorRole.SYSTEM,
                name=None,
                items=[
                    TextContent(
                        inner_content=None,
                        ai_model_id=None,
                        metadata={},
                        content_type=ContentTypes.TEXT_CONTENT,
                        text='System message',
                        encoding=None
                    )
                ],
                encoding=None,
                finish_reason=None
            ),
            ChatMessageContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type=ContentTypes.CHAT_MESSAGE_CONTENT,
                role=AuthorRole.USER,
                name=None,
                items=[
                    TextContent(
                        inner_content=None,
                        ai_model_id=None,
                        metadata={},
                        content_type=ContentTypes.TEXT_CONTENT,
                        text='Hello',
                        encoding=None
                    )
                ],
                encoding=None,
                finish_reason=None
            ),
            ChatMessageContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type=ContentTypes.CHAT_MESSAGE_CONTENT,
                role=AuthorRole.ASSISTANT,
                name=None,
                items=[],
                encoding=None,
                finish_reason=None
            ),
            ChatMessageContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type=ContentTypes.CHAT_MESSAGE_CONTENT,
                role=AuthorRole.USER,
                name=None,
                items=[
                    TextContent(
                        inner_content=None,
                        ai_model_id=None,
                        metadata={},
                        content_type=ContentTypes.TEXT_CONTENT,
                        text='test',
                        encoding=None
                    )
                ],
                encoding=None,
                finish_reason=None
            ),
            ChatMessageContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type=ContentTypes.CHAT_MESSAGE_CONTENT,
                role=AuthorRole.ASSISTANT,
                name=None,
                items=[
                    TextContent(
                        inner_content=None,
                        ai_model_id=None,
                        metadata={},
                        content_type=ContentTypes.TEXT_CONTENT,
                        text='Hi, how can I help?',
                        encoding=None
                    )
                ],
                encoding=None,
                finish_reason=None
            )
        ]
        self.assertEqual(self.chat_history.internal_messages, expected_internal_messages)
        self.assertEqual(self.chat_history.messages, expected_messages)

    def test_read_messages_with_tool_call_when_no_remove_tool_calls_prunes_messages(self):
        session_id = "session123"
        user_id = "user456"
        mock_doc = {
            "id": session_id,
            "user_id": user_id,
            "domain": self.domain,
            "subdomain": self.subdomain,
            "messages": [
                {
                    "role": "system",
                    "content": "System message",
                    "type": "internal",
                    "data": {"content": "System message"}
                },
                {
                    "role": "user",
                    "content": "Hello",
                    "type": "human",
                    "data": {"content": "Hello"}
                },
                {
                    "role": "assistant",
                    "content": "",
                    "type": "ai",
                    "data": {"content": ""}
                },
                {
                    "role": "user",
                    "content": "test",
                    "type": "human",
                    "data": {"content": "test"}
                },
                {
                    "role": "tool",
                    "items": [
                        {
                            "metadata": {},
                            "content_type": "function_result",
                            "id": "test",
                            "result": "test",
                            "name": "test",
                            "function_name": "test_fn",
                            "plugin_name": "Function",
                        }
                    ],
                    "type": "internal",
                    "data": {
                        "content": ""
                    }
                },
                {
                    "role": "assistant",
                    "content": "Hi, how can I help?",
                    "type": "ai",
                    "data": {"content": ""}
                }
            ]
        }

        self.mock_container.read_item.return_value = mock_doc
        self.chat_history.remove_tool_calls = False
        self.chat_history.read_messages(session_id, user_id)
        self.mock_container.read_item.assert_called_once_with(
            item=session_id,
            partition_key=[user_id, self.domain, self.subdomain]
        )
        expected_messages = [
            ChatMessageContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type=ContentTypes.CHAT_MESSAGE_CONTENT,
                role=AuthorRole.SYSTEM,
                name=None,
                items=[
                    TextContent(
                        inner_content=None,
                        ai_model_id=None,
                        metadata={},
                        content_type=ContentTypes.TEXT_CONTENT,
                        text='System message',
                        encoding=None
                    )
                ],
                encoding=None,
                finish_reason=None
            ),
            ChatMessageContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type=ContentTypes.CHAT_MESSAGE_CONTENT,
                role=AuthorRole.USER,
                name=None,
                items=[
                    TextContent(
                        inner_content=None,
                        ai_model_id=None,
                        metadata={},
                        content_type=ContentTypes.TEXT_CONTENT,
                        text='Hello',
                        encoding=None
                    )
                ],
                encoding=None,
                finish_reason=None
            ),
            ChatMessageContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type=ContentTypes.CHAT_MESSAGE_CONTENT,
                role=AuthorRole.ASSISTANT,
                name=None,
                items=[],
                encoding=None,
                finish_reason=None
            ),
            ChatMessageContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type=ContentTypes.CHAT_MESSAGE_CONTENT,
                role=AuthorRole.USER,
                name=None,
                items=[
                    TextContent(
                        inner_content=None,
                        ai_model_id=None,
                        metadata={},
                        content_type=ContentTypes.TEXT_CONTENT,
                        text='test',
                        encoding=None
                    )
                ],
                encoding=None,
                finish_reason=None
            ),
            ChatMessageContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type=ContentTypes.CHAT_MESSAGE_CONTENT,
                role=AuthorRole.TOOL,
                name=None,
                items=[
                    FunctionResultContent(
                        inner_content=None,
                        ai_model_id=None,
                        metadata={},
                        content_type=ContentTypes.FUNCTION_RESULT_CONTENT,
                        id='test',
                        result='test',
                        name='test',
                        function_name='test_fn',
                        plugin_name='Function',
                        encoding=None
                    )
                ],
                encoding=None,
                finish_reason=None
            ),
            ChatMessageContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type=ContentTypes.CHAT_MESSAGE_CONTENT,
                role=AuthorRole.ASSISTANT,
                name=None,
                items=[
                    TextContent(
                        inner_content=None,
                        ai_model_id=None,
                        metadata={},
                        content_type=ContentTypes.TEXT_CONTENT,
                        text='Hi, how can I help?',
                        encoding=None
                    )
                ],
                encoding=None,
                finish_reason=None
            )
        ]

        self.assertEqual(self.chat_history.internal_messages, expected_messages)
        self.assertEqual(self.chat_history.messages, expected_messages)

    def test_read_messages_with_tool_call_full_messages(self):
        session_id = "session123"
        user_id = "user456"
        mock_doc = {
            "id": session_id,
            "user_id": user_id,
            "domain": self.domain,
            "subdomain": self.subdomain,
            "messages": [
                {
                    "role": "system",
                    "content": "System message",
                    "type": "internal",
                    "data": {"content": "System message"}
                },
                {
                    "role": "user",
                    "content": "test",
                    "type": "human",
                    "data": {"content": "test"}
                },
                {
                    "role": "tool",
                    "items": [
                        {
                            "metadata": {},
                            "content_type": "function_result",
                            "id": "test",
                            "result": "test",
                            "name": "test",
                            "function_name": "test_fn",
                            "plugin_name": "Function",
                        }
                    ],
                    "type": "internal",
                    "data": {
                        "content": ""
                    }
                },
                {
                    "role": "assistant",
                    "content": "Hi, how can I help?",
                    "type": "ai",
                    "data": {"content": ""}
                }
            ]
        }
        self.mock_container.read_item.return_value = mock_doc
        self.chat_history.read_messages(session_id, user_id)
        self.mock_container.read_item.assert_called_once_with(
            item=session_id,
            partition_key=[user_id, self.domain, self.subdomain]
        )
        expected_messages = [
            ChatMessageContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type=ContentTypes.CHAT_MESSAGE_CONTENT,
                role=AuthorRole.SYSTEM,
                name=None,
                items=[
                    TextContent(
                        inner_content=None,
                        ai_model_id=None,
                        metadata={},
                        content_type=ContentTypes.TEXT_CONTENT,
                        text='System message',
                        encoding=None
                    )
                ],
                encoding=None,
                finish_reason=None
            ),
            ChatMessageContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type=ContentTypes.CHAT_MESSAGE_CONTENT,
                role=AuthorRole.USER,
                name=None,
                items=[
                    TextContent(
                        inner_content=None,
                        ai_model_id=None,
                        metadata={},
                        content_type=ContentTypes.TEXT_CONTENT,
                        text='test',
                        encoding=None
                    )
                ],
                encoding=None,
                finish_reason=None
            ),
            ChatMessageContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type=ContentTypes.CHAT_MESSAGE_CONTENT,
                role=AuthorRole.TOOL,
                name=None,
                items=[
                    FunctionResultContent(
                        inner_content=None,
                        ai_model_id=None,
                        metadata={},
                        content_type=ContentTypes.FUNCTION_RESULT_CONTENT,
                        id='test',
                        result='test',
                        name='test',
                        function_name='test_fn',
                        plugin_name='Function',
                        encoding=None
                    )
                ],
                encoding=None,
                finish_reason=None
            ),
            ChatMessageContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type=ContentTypes.CHAT_MESSAGE_CONTENT,
                role=AuthorRole.ASSISTANT,
                name=None,
                items=[
                    TextContent(
                        inner_content=None,
                        ai_model_id=None,
                        metadata={},
                        content_type=ContentTypes.TEXT_CONTENT,
                        text='Hi, how can I help?',
                        encoding=None
                    )
                ],
                encoding=None,
                finish_reason=None
            )
        ]

        self.assertEqual(self.chat_history.internal_messages, expected_messages)
        self.assertEqual(self.chat_history.messages, expected_messages)

    def test_read_messages_no_session_found(self):
        session_id = "nonexistent_session"
        user_id = "user456"

        self.mock_container.read_item.side_effect = CosmosHttpResponseError(status_code=404)

        with patch("services.cosmos_chat_history.logging") as mock_logging:
            self.chat_history.read_messages(session_id, user_id)
            mock_logging.info.assert_called_once_with("no session found")

        self.assertEqual(self.chat_history.messages, [])
        self.assertEqual(self.chat_history.internal_messages, [])


class TestCosmosChatHistoryUserMessageLimitExceeded(unittest.TestCase):
    def setUp(self):
        self.mock_container = Mock(spec=ContainerProxy)
        self.domain = "test_domain"
        self.subdomain = "test_subdomain"
        self.chat_history = CosmosChatHistory(
            container=self.mock_container,
            user_message_limit=2,
            domain=self.domain,
            subdomain=self.subdomain
        )

    def test_user_message_limit_not_exceeded(self):
        self.chat_history.internal_messages = [
            ChatMessageContent(role=AuthorRole.USER, content="Hello"),
            ChatMessageContent(role=AuthorRole.ASSISTANT, content="Hi, how can I help?")
        ]

        self.assertFalse(self.chat_history.user_message_limit_exceeded)

    def test_user_message_limit_exceeded(self):
        self.chat_history.internal_messages = [
            ChatMessageContent(role=AuthorRole.USER, content="Hello"),
            ChatMessageContent(role=AuthorRole.ASSISTANT, content="Hi, how can I help?"),
            ChatMessageContent(role=AuthorRole.USER, content="Another question"),
            ChatMessageContent(role=AuthorRole.USER, content="Yet another question")
        ]

        self.assertTrue(self.chat_history.user_message_limit_exceeded)


class TestCosmosChatHistoryAddMessage(unittest.TestCase):
    """Tests for the add_message method of CosmosChatHistory class."""

    def setUp(self):
        """Set up the test environment before each test."""
        self.mock_container = Mock(spec=ContainerProxy)
        self.domain = "test_domain"
        self.subdomain = "test_subdomain"
        self.chat_history = CosmosChatHistory(
            container=self.mock_container,
            user_message_limit=20,
            domain=self.domain,
            subdomain=self.subdomain
        )

    def test_add_message_chatmessagecontent(self):
        """Test adding a ChatMessageContent instance."""
        # Arrange
        message = ChatMessageContent(role=AuthorRole.USER, content="Test message")

        # Act
        self.chat_history.add_message(message)

        # Assert
        self.assertEqual(len(self.chat_history.internal_messages), 1)
        self.assertEqual(len(self.chat_history.messages), 1)
        self.assertEqual(self.chat_history.internal_messages[0], message)
        self.assertEqual(self.chat_history.messages[0], message)

    def test_add_message_dict_minimal(self):
        """Test adding a minimal dictionary with only required fields."""
        # Arrange
        message_dict = {"role": "user", "content": "Test message"}

        # Act
        self.chat_history.add_message(message_dict)

        # Assert
        self.assertEqual(len(self.chat_history.internal_messages), 1)
        self.assertEqual(len(self.chat_history.messages), 1)
        self.assertEqual(self.chat_history.internal_messages[0].role, AuthorRole.USER)
        self.assertEqual(self.chat_history.internal_messages[0].content, "Test message")
        self.assertEqual(self.chat_history.messages[0].role, AuthorRole.USER)
        self.assertEqual(self.chat_history.messages[0].content, "Test message")

    def test_add_message_dict_with_encoding(self):
        """Test adding a dictionary with encoding parameter."""
        # Arrange
        message_dict = {"role": "assistant", "content": "Test response"}
        encoding = "utf-8"

        # Act
        self.chat_history.add_message(message_dict, encoding=encoding)

        # Assert
        self.assertEqual(len(self.chat_history.internal_messages), 1)
        self.assertEqual(len(self.chat_history.messages), 1)
        self.assertEqual(self.chat_history.internal_messages[0].role, AuthorRole.ASSISTANT)
        self.assertEqual(self.chat_history.internal_messages[0].content, "Test response")
        self.assertEqual(self.chat_history.internal_messages[0].encoding, encoding)
        self.assertEqual(self.chat_history.messages[0].role, AuthorRole.ASSISTANT)
        self.assertEqual(self.chat_history.messages[0].content, "Test response")
        self.assertEqual(self.chat_history.messages[0].encoding, encoding)
        self.assertEqual(self.chat_history.messages[0].encoding, encoding)

    def test_add_message_dict_with_metadata(self):
        """Test adding a dictionary with metadata parameter."""
        # Arrange
        message_dict = {"role": "user", "content": "Test message"}
        metadata = {"timestamp": "2025-05-14T12:00:00Z"}

        # Act
        self.chat_history.add_message(message_dict, metadata=metadata)

        # Assert
        self.assertEqual(len(self.chat_history.internal_messages), 1)
        self.assertEqual(len(self.chat_history.messages), 1)
        self.assertEqual(self.chat_history.internal_messages[0].metadata, metadata)
        self.assertEqual(self.chat_history.messages[0].metadata, metadata)

    def test_add_message_multiple_messages(self):
        """Test adding multiple messages in sequence."""
        # Arrange
        message1 = ChatMessageContent(role=AuthorRole.USER, content="User message")
        message2 = ChatMessageContent(role=AuthorRole.ASSISTANT, content="Assistant response")

        # Act
        self.chat_history.add_message(message1)
        self.chat_history.add_message(message2)

        # Assert
        self.assertEqual(len(self.chat_history.internal_messages), 2)
        self.assertEqual(len(self.chat_history.messages), 2)
        self.assertEqual(self.chat_history.internal_messages[0], message1)
        self.assertEqual(self.chat_history.internal_messages[1], message2)
        self.assertEqual(self.chat_history.messages[0], message1)
        self.assertEqual(self.chat_history.messages[1], message2)

    def test_add_message_missing_role(self):
        """Test that adding a dictionary without a role raises an error."""
        # Arrange
        message_dict = {"content": "Missing role"}

        # Act & Assert
        with self.assertRaises(ContentInitializationError):
            self.chat_history.add_message(message_dict)

        # Verify no messages were added
        self.assertEqual(len(self.chat_history.internal_messages), 0)
        self.assertEqual(len(self.chat_history.messages), 0)

    def test_add_message_system_role(self):
        """Test adding a message with system role."""
        # Arrange
        message = ChatMessageContent(role=AuthorRole.SYSTEM, content="System instruction")

        # Act
        self.chat_history.add_message(message)

        # Assert
        self.assertEqual(len(self.chat_history.internal_messages), 1)
        self.assertEqual(len(self.chat_history.messages), 1)
        self.assertEqual(self.chat_history.internal_messages[0].role, AuthorRole.SYSTEM)
