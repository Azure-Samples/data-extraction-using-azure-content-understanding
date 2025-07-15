from typing import Literal
from pydantic import BaseModel
from datetime import date
from enum import Enum
from typing import Optional


class IngestDocumentType(str, Enum):
    COLLECTION = "Collection"


class BaseIngestDocumentRequest(BaseModel):
    id: str
    type: IngestDocumentType
    filename: str
    file_bytes: bytes
    date_of_document: date
    lease_id: Optional[str] = None


class IngestCollectionDocumentRequest(BaseIngestDocumentRequest):
    type: Literal[IngestDocumentType.COLLECTION] = IngestDocumentType.COLLECTION
    lease_id: str
