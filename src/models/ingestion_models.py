from typing import Literal
from pydantic import BaseModel
from datetime import date
from enum import Enum
from typing import Optional


class IngestDocumentType(str, Enum):
    MLA = "MLA"
    SITE = "Site"


class BaseIngestDocumentRequest(BaseModel):
    id: str
    type: IngestDocumentType
    filename: str
    file_bytes: bytes
    date_of_document: date
    market: Optional[str] = None
    lease_id: Optional[str] = None


class MLAIngestDocumentRequest(BaseIngestDocumentRequest):
    type: Literal[IngestDocumentType.MLA] = IngestDocumentType.MLA
    market: Literal[None] = None
    lease_id: Literal[None] = None


class SiteIngestDocumentRequest(BaseIngestDocumentRequest):
    type: Literal[IngestDocumentType.SITE] = IngestDocumentType.SITE
    market: str
    lease_id: str
