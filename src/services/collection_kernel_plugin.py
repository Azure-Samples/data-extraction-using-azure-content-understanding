from collections import defaultdict
from semantic_kernel.functions import kernel_function
from datetime import date, datetime
from typing import Optional
import json
from models.data_collection_config import DataType, \
    FieldDataCollectionConfig, \
    LeaseAgreementCollectionRow
from models.document_data_models import LeaseAgreement, DocumentData
from services.ingest_lease_documents_service import IngestionCollectionDocumentService
from cachetools import TTLCache
from cachetools.keys import hashkey
from services.citation_mapper import CitationMapper

document_data_cache = TTLCache(maxsize=100, ttl=86400)


def convert_datetime(o):
    """Converts datetime and date objects to their string representation.

    Args:
        o: The object to convert.

    Returns:
        str: The string representation of the datetime or date object, or the original object if not
    """
    if isinstance(o, datetime) or isinstance(o, date):
        return o.__str__()


class CollectionPlugin:
    """This class provides methods to initialize the plugin to retrieve collection data based on a collection ID."""
    _config: FieldDataCollectionConfig
    _document_service: IngestionCollectionDocumentService
    _collection_id: Optional[str] = None

    def __init__(self, config: FieldDataCollectionConfig,
                 document_service: IngestionCollectionDocumentService):
        """Initializes the CollectionPlugin with the given configuration."""
        self._config = config
        self._document_service = document_service
        self._citation_mapper = CitationMapper()

    def composite_key(self, collection_id: str, lease_config_hash: str):
        """Generates a composite key by hashing the provided collection ID and lease configuration hash.

        Args:
            collection_id (str): The unique identifier for the collection.
            lease_config_hash (str): The hash of the lease configuration.

        Returns:
            hash: A hash object representing the composite key.
        """
        return hashkey(collection_id, lease_config_hash)

    @kernel_function(
        name="get_collection_data",
        description="Gets the data for a specified collection by the collection id.",
    )
    def get_collection_data(
        self,
        collection_id: str,
    ) -> str:
        """Gets the data for a specified collection by the collection id."""
        # Generate a composite key for caching
        self._collection_id = collection_id
        cache_key = self.composite_key(collection_id, self._config.lease_config_hash)

        # Check if the data is already in the cache
        if cache_key in document_data_cache:
            document_data_str = document_data_cache[cache_key]["document_data_str"]
            citation_mappings = document_data_cache[cache_key]["citation_mappings"]
        else:
            # Fetch structured and unstructured data leases
            unstructured_data = self._get_unstructured_data_lease_info_by_collection_id(collection_id)

            # Create the document data object
            document_data = DocumentData(
                _id=collection_id,
                lease_config_hash=self._config.lease_config_hash,
                unstructured_data=unstructured_data,
            )
            document_data = document_data.model_dump(
                by_alias=True,
                exclude_none=True,
                exclude_defaults=True,
                exclude_unset=True,
            )

            document_data, citation_mappings = self._citation_mapper.process_json(document_data)

            # Serialize the document data to a string
            document_data_str = json.dumps(document_data, default=convert_datetime)

        # Store the result in the cache
        document_data_cache[cache_key] = {
            "document_data_str": document_data_str,
            "citation_mappings": citation_mappings
        }

        return document_data_str

    def _get_unstructured_data_lease_info_by_collection_id(self, collection_id: str) -> list[LeaseAgreement]:
        """Queries CosmosDB to retrieve extracted lease information for the specified collection ID.

        Args:
            collection_id (str): Collection ID to query

        Returns:
            list[LeaseAgreement]: list of LeaseAgreements containing the fields extracted from
                                  raw lease documents using Azure AI Content Understanding
        """
        unstructured_data_leases = []
        lease_document_rows: list[LeaseAgreementCollectionRow] = \
            [row for row in self._config.collection_rows if row.data_type == DataType.LEASE_AGREEMENT]

        if len(lease_document_rows) > 0:
            extracted_fields = self._document_service._get_all_extracted_fields_from_collection_doc(collection_id,
                                                                                                     self._config)

            unstructured_data_leases = [LeaseAgreement(lease_id=lease_id, fields=lease_fields)
                                        for lease_id, lease_fields in extracted_fields.items()]

        return unstructured_data_leases

    def _get_original_citation(self, citation: str) -> str:
        """Extracts the original collection ID from the citation string.

        Args:
            citation (str): Citation string in the format 'CITE{collection_id}-{alias}'.

        Returns:
            str: Extracted collection ID.
        """
        # Citation is in the format of CITE{collection_id}-{alias}. Extract the collection ID.
        # Validate the citation format in list-like string
        if citation.startswith("[") and citation.endswith("]"):
            try:
                citation_list = json.loads(citation)
                if isinstance(citation_list, list):
                    citation = citation_list[0]
            except Exception:
                raise ValueError(
                    "Invalid citation format. Expected format: '['CITE{collection_id}-{alias}'].")

        if not citation.startswith("CITE") or "-" not in citation:
            raise ValueError("Invalid citation format. Expected format: 'CITE{collection_id}-{alias}'.")

        # Extract and return the collection ID
        collection_id = citation.split('-')[0][4:]

        key = self.composite_key(collection_id, self._config.lease_config_hash)

        if citation not in document_data_cache[key]['citation_mappings']:
            return None

        restored_citation = document_data_cache[key]['citation_mappings'][citation]

        return [restored_citation['source_document'], restored_citation['source_bounding_boxes']]

    def restore_citations(self, citations: list[str]):
        """Restores the original form of a list of citations.

        This method takes a list of citations, processes each citation to retrieve
        its original form, and returns a new list containing the restored citations.

        Args:
            citations (list[str]): A list of citation strings to be restored.

        Returns:
            list[str]: A list of citations in their original form.
        """
        new_citations = []
        for citation in citations:
            new_citation = self._get_original_citation(citation)

            if new_citation:
                new_citations.append(new_citation)

        return new_citations
