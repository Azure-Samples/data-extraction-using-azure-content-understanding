from pydantic import BaseModel
from typing import Any, Dict, Optional
from semantic_kernel.kernel_pydantic import KernelBaseModel


class QueryRequest(BaseModel):
    """QueryRequest model for API requests."""
    cid: str  # Correlation ID
    sid: str  # Session ID
    query: str
    model: Optional[str] = None


class GeneratedResponse(KernelBaseModel):
    """GeneratedResponse model for formatted response from Semantic Kernel.

    Attributes:
            response (str): The main response text. Always include the inline citation number in the response text,
                e.g., 'The termination rights for collection document 123 has been waived any unilateral termination rights[1]'."
            citations (list): A list of citations. For example, ["CITECH75442D-2, "CITECH75442D-3]
    """
    response: str
    citations: list[str]


class QueryMetrics(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    total_latency_sec: float


class QueryResponse(BaseModel):
    """QueryResponse model for API responses.

    Attributes:
            response (str): The main response text. Always include the inline citation number in the response text,
                e.g., 'The termination rights for site CH75442D has been waived any unilateral termination rights[1]'."
            citations (list): A list of citations in the format ["source_document", "source_bounding_boxes"].
    """
    response: str
    citations: list[list[str]]
    metrics: Optional[QueryMetrics] = None
    metadata: Dict[str, Any] = {}
