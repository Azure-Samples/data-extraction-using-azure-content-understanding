from typing import Optional
from models.ingestion_models import IngestDocumentType
from constants import PathConstants


def build_adls_markdown_file_path(
    doc_type: IngestDocumentType,
    id: str,
    file_name: str,
    market: Optional[str],
    lease_id: Optional[str],
):
    """Build the markdown file path for the given parameters.

    Args:
        doc_type (IngestDocumentType): The document type.
        market (str): The market name.
        id (str): The ID of the document.
        lease_id (str): The lease ID.
        file_name (str): The file name.

    Returns:
        str: The constructed markdown file path.
    """
    if not file_name.endswith(".md"):
        file_name = file_name.split(".")[0] + ".md"

    if market is None:
        raise ValueError("Market must be provided for COLLECTION document type.")
    if lease_id is None:
        raise ValueError("Lease ID must be provided for COLLECTION document type.")

    return f"{PathConstants.COLLECTION_PREFIX}/{market}/{id}/{lease_id}/{file_name}"


def build_adls_pdf_file_path(
    doc_type: IngestDocumentType,
    id: str,
    file_name: str,
    market: Optional[str],
    lease_id: Optional[str]
):
    """Build the PDF file path for the given parameters.

    Args:
        doc_type (IngestDocumentType): The document type.
        market (str): The market name.
        id (str): The ID of the document.
        lease_id (str): The lease ID.
        file_name (str): The file name.

    Returns:
        str: The constructed PDF file path.
    """
    if not file_name.endswith(".pdf"):
        file_name = file_name.split(".")[0] + ".pdf"

    if market is None:
        raise ValueError("Market must be provided for COLLECTION document type.")
    if lease_id is None:
        raise ValueError("Lease ID must be provided for COLLECTION document type.")

    return f"{PathConstants.COLLECTION_PREFIX}/{market}/{id}/{lease_id}/{file_name}"
