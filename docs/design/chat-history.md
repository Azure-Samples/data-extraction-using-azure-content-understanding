# Chat History Management

## Overview

This document outlines the design and implementation details for managing chat history within this project's query functionality. Maintaining chat history provides essential context, enabling a more natural conversational flow and enhancing the overall user experience. By preserving previous interactions, the system can deliver more accurate and contextually relevant responses, resulting in a more intuitive and conversational interaction.

## Design

The chat history management process consists of two primary operations:

- **Persisting Chat History**: Storing user interactions and assistant responses.
- **Retrieving Chat History**: Fetching previous interactions to provide context for ongoing conversations.

## Persisting Chat History

Chat history is persisted to ensure continuity, context-awareness in user interactions, and accurate usage tracking. Each conversation is uniquely identified by a session ID (`sid`) provided in the request payload. The session ID groups related messages into a single conversation thread, in conjunction with the domain, subdomain, and user ID.

The request payload structure is as follows:

```json
{
    "cid": "<correlation-id-from-frontend",
    "sid": "<session-id>",
    "query": "User's query text"
}
```

- **`cid`**: A unique identifier representing the request, as propagated by the frontend.
- **`sid`**: A unique identifier representing the user's conversation session.
- **`query`**: The user's input or question.

The user ID is extracted from the `x-user` header included in the HTTP request. This header must be provided by the client application.

The chat history is stored in Azure Cosmos DB with the following structure:

```json
{
    "sid": "<session-id>",
    "user_id": "<user-id>",
    "domain": "<domain>",
    "subdomain": "",
    "messages": [
        // messages...
    ]
}
```

- **`sid`**: Unique identifier for the conversation session.
- **`user_id`**: Identifier of the user who initiated the query.
- **`domain`**: The domain context.
- **`subdomain`**: The sub-domain context (currently empty by default).
- **`messages`**: Chronological list of interactions between the user and the assistant.

The chat history is updated after each successful assistant response, ensuring the conversation context remains current.

## Retrieving Chat History

When initiating or continuing a conversation, the system retrieves existing chat history from Azure Cosmos DB using the provided session ID (`sid`), user ID (extracted from the `x-user` header), and domain. This retrieval provides context for the assistant, enabling more natural and coherent interactions.


The retrieval process involves:

1. Extracting the session ID from the request payload.
2. Extracting the user ID from the `x-user` header.
3. Querying Azure Cosmos DB for existing chat history matching the session ID, user ID, domain, and subdomain, retrieving only the most recent messages (top k messages).
4. Loading the retrieved messages into the conversation context for use by the assistant.

If no existing chat history is found, a new conversation context is initialized.

This approach ensures the assistant maintains context across multiple interactions, providing a more natural and coherent conversational experience for the user.

## Deletion Operations

The user interface supports two distinct deletion operations for managing chat history:

1. **Deletion by Session**
2. **Deletion by Individual Message**

### Deletion by Session

When a user initiates a session deletion through the UI, the session data is cleared from the user interface view. However, the corresponding data will **not** be deleted from Azure Cosmos DB and will remain stored in the database.

### Deletion by Individual Message

When a user deletes an individual message through the UI, the message is removed from the user interface view only. The message itself will **not** be deleted from Azure Cosmos DB and will remain stored in the database.

## Session Constraints

To maintain optimal performance and ensure efficient management of chat history, each conversation session is limited to a configurable maximum number of user questions. By default, this limit is set to 20 user questions. This constraint helps prevent performance degradation caused by excessively long conversation threads and ensures a responsive user experience.

When a session reaches this configured limit, the service will respond with an HTTP status code `400 Bad Request` and a message of `User message limit exceeded.`, indicating that the maximum number of questions for the current session has been reached. At this point, users must initiate a new session to continue interacting with the assistant.

Please note that context from the previous session does not propagate into the new session. Consequently, the new session will not retain any prior context, including previously asked questions or referenced collection IDs. Users should be aware that starting a new session effectively resets the conversation context.
