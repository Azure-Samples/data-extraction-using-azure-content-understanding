from typing import Any, Literal, Optional, List, Dict
from enum import Enum
from datetime import date
from pydantic import BaseModel, Field
from .extracted_collection_documents import ExtractedLeaseFieldValue


class DocumentType(str, Enum):
    LEASE_AGREEMENT = "LeaseAgreement"


class FieldMappingType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    TIME = "time"
    OBJECT = "object"
    ARRAY = "array"


class CollectedDocumentData(BaseModel):
    document_type: DocumentType


class _LeaseAgreementDocumentData(ExtractedLeaseFieldValue):
    source_document: Optional[str] = Field(default="", alias='document')
    source_bounding_boxes: Optional[str] = Field(default=None, alias='source')
    date_of_document: Optional[date] = None

    # override the fields to get the source and source bounding box
    valueArray: Optional[List["_LeaseAgreementDocumentData"]] = None  # Recursive type
    valueObject: Optional[Dict[str, "_LeaseAgreementDocumentData"]] = None  # Recursive type

    class Config:
        populate_by_name = True
        extra = "ignore"


_LeaseAgreementDocumentData.model_rebuild()


class LeaseAgreementDocumentData(CollectedDocumentData, _LeaseAgreementDocumentData):
    document_type: DocumentType = DocumentType.LEASE_AGREEMENT

    class Config:
        """The config for the LeaseAgreementDocumentData model."""
        populate_by_name = True
        extra = "ignore"


class LeaseAgreement(BaseModel):
    lease_id: Optional[str] = None
    original_documents: list[str] = []
    markdown_documents: list[str] = []
    fields: dict[str, List[LeaseAgreementDocumentData]]


class DocumentData(BaseModel):
    id: str = Field(..., alias='_id')
    lease_config_hash: str
    unstructured_data: list[LeaseAgreement]
