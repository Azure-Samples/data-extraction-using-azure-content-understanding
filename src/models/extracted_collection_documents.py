from datetime import date
from enum import Enum
from typing import Any, Optional, List, Dict
from uuid import uuid4

from pydantic import BaseModel, Field
from .base_mongo_lockable import BaseMongoLockable


class ExtractedLeaseFieldType(str, Enum):
    """Type of the extracted field."""
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    DATE = "date"
    TIME = "time"
    ARRAY = "array"
    OBJECT = "object"


class ExtractedLeaseFieldValue(BaseModel):
    """Representation of a field value in a lease document."""
    valueString: Optional[str] = None
    valueNumber: Optional[float] = None
    valueInteger: Optional[int] = None
    valueDate: Optional[str] = None
    valueTime: Optional[str] = None
    valueArray: Optional[List["ExtractedLeaseFieldValue"]] = None  # Recursive type
    valueObject: Optional[Dict[str, "ExtractedLeaseFieldValue"]] = None  # Recursive type


ExtractedLeaseFieldValue.model_rebuild()


class ExtractedLeaseField(ExtractedLeaseFieldValue):
    """Representation of a field in a lease document."""
    type: ExtractedLeaseFieldType
    valueArray: Optional[List["ExtractedLeaseField"]] = None  # Recursive type
    valueObject: Optional[Dict[str, "ExtractedLeaseField"]] = None  # Recursive type
    spans: List[Dict[str, Any]] = []
    confidence: Optional[float] = None
    source: Optional[str] = None
    date_of_document: Optional[date] = None
    markdown: Optional[str] = None
    document: Optional[str] = None
    category: Optional[str] = None
    subdocument_start_page: Optional[int] = None
    subdocument_end_page: Optional[int] = None


ExtractedLeaseField.model_rebuild()


class ExtractedLeaseCollection(BaseModel):
    """Representation of a lease document."""
    lease_id: Optional[str] = None
    original_documents: list[str]
    markdowns: list[str]  # List of markdown documents stored in Azure Blob Storage
    fields: dict[str, list[ExtractedLeaseField]]


class ExtractedCollectionInformationCollection(BaseModel):
    """Representation of the information section in a document."""
    leases: list[ExtractedLeaseCollection]


class ExtractedCollectionDocuments(BaseMongoLockable):
    """Representation of the entire document."""
    id: str = Field(..., alias="_id", default_factory=lambda: str(uuid4()))
    collection_id: str
    config_id: str
    lease_config_hash: str
    information: ExtractedCollectionInformationCollection
