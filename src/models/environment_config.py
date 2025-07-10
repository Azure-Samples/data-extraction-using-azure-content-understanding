from pydantic import BaseModel, model_validator
from enum import Enum
from typing import Optional
from typing_extensions import TypeVar, Generic


T = TypeVar("T", default=str)


class ConfigurationType(str, Enum):
    VALUE = "value"
    SECRET = "secret"


class ConfigurationValue(BaseModel, Generic[T]):
    value: Optional[T] = None
    key: Optional[str] = None
    type: ConfigurationType = ConfigurationType.VALUE

    @model_validator(mode="after")
    def check_key_or_value(cls, values):
        type = values.type or ConfigurationType.VALUE
        if type == ConfigurationType.VALUE and values.value is None:
            raise ValueError("Value must be provided when type is 'value'")

        if type == ConfigurationType.SECRET and values.key is None:
            raise ValueError("Key must be provided when type is 'secret'")
        return values


class UserManagedIdentityConfig(BaseModel):
    client_id: Optional[ConfigurationValue] = None


class CosmosDbConfig(BaseModel):
    db_name: ConfigurationValue
    endpoint: ConfigurationValue
    configuration_collection_name: ConfigurationValue
    document_collection_name: ConfigurationValue


class LLMConfig(BaseModel):
    model_name: ConfigurationValue
    endpoint: ConfigurationValue
    access_key: ConfigurationValue
    api_version: ConfigurationValue


class DefaultIngestConfig(BaseModel):
    name: ConfigurationValue
    version: ConfigurationValue


class ContentUnderstandingConfig(BaseModel):
    endpoint: ConfigurationValue
    subscription_key: ConfigurationValue
    request_timeout: Optional[ConfigurationValue[int]] = None
    project_id: ConfigurationValue


class ChatHistoryConfig(BaseModel):
    endpoint: ConfigurationValue
    key: Optional[ConfigurationValue] = None
    db_name: ConfigurationValue
    chat_history_container_name: ConfigurationValue
    user_message_limit: ConfigurationValue[int]
    domain: ConfigurationValue
    remove_tool_calls: ConfigurationValue[str] = ConfigurationValue(value="true")


class BlobStorageConfig(BaseModel):
    account_url: ConfigurationValue
    container_name: ConfigurationValue


class EnvironmentConfig(BaseModel):
    key_vault_uri: str
    user_managed_identity: UserManagedIdentityConfig
    tenant_id: str
    cosmosdb: CosmosDbConfig
    llm: LLMConfig
    default_ingest_config: DefaultIngestConfig
    content_understanding: ContentUnderstandingConfig
    chat_history: ChatHistoryConfig
    blob_storage: BlobStorageConfig
