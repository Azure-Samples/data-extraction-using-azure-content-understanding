from collections import defaultdict
from semantic_kernel.functions import kernel_function
from datetime import date, datetime
from typing import Optional
import json
from models.data_collection_config import DataType, \
    FieldDataCollectionConfig, \
    LeaseAgreementCollectionRow
from models.document_data_models import LeaseAgreement, DocumentData
from services.ingest_lease_documents_service import IngestionSiteLeaseService
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


class SitePlugin:
    """This class provides methods to initialize the plugin to retrieve site data based on a site ID."""
    _config: FieldDataCollectionConfig
    _lease_documents_service: IngestionSiteLeaseService
    _site_id: Optional[str] = None

    def __init__(self, config: FieldDataCollectionConfig,
                 lease_documents_service: IngestionSiteLeaseService):
        """Initializes the SitePlugin with the given configuration."""
        self._config = config
        self._lease_documents_service = lease_documents_service
        self._citation_mapper = CitationMapper()

    def composite_key(self, site_id: str, lease_config_hash: str):
        """Generates a composite key by hashing the provided site ID and lease configuration hash.

        Args:
            site_id (str): The unique identifier for the site.
            lease_config_hash (str): The hash of the lease configuration.

        Returns:
            hash: A hash object representing the composite key.
        """
        return hashkey(site_id, lease_config_hash)

    @kernel_function(
        name="get_site_data",
        description="Gets the data for a specified site by the site id or mla id.",
    )
    def get_site_data(
        self,
        site_id: str,
    ) -> str:
        """Gets the data for a specified site by the site id."""
        # Generate a composite key for caching
        self._site_id = site_id
        cache_key = self.composite_key(site_id, self._config.lease_config_hash)

        # Check if the data is already in the cache
        if cache_key in document_data_cache:
            document_data_str = document_data_cache[cache_key]["document_data_str"]
            citation_mappings = document_data_cache[cache_key]["citation_mappings"]
        else:
            # Fetch structured and unstructured data leases
            unstructured_data_leases = self._get_unstructured_data_lease_info_by_site_id(site_id)

            # Create the document data object
            document_data = DocumentData(
                _id=site_id,
                lease_config_hash=self._config.lease_config_hash,
                leases_from_structured_data=[],  # This will be populated later
                leases_from_unstructured_data=unstructured_data_leases,
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

    def _get_unstructured_data_lease_info_by_site_id(self, site_id: str) -> list[LeaseAgreement]:
        """Queries CosmosDB to retrieve extracted lease information for the specified site ID.

        Args:
            site_id (str): Site ID to query

        Returns:
            list[LeaseAgreement]: list of LeaseAgreements containing the fields extracted from
                                  raw lease documents using Azure AI Content Understanding
        """
        unstructured_data_leases = []
        lease_document_rows: list[LeaseAgreementCollectionRow] = \
            [row for row in self._config.collection_rows if row.data_type == DataType.LEASE_AGREEMENT]

        if len(lease_document_rows) > 0:
            extracted_fields = self._lease_documents_service._get_all_extracted_fields_from_site_doc(site_id,
                                                                                                     self._config)

            unstructured_data_leases = [LeaseAgreement(lease_id=lease_id, fields=lease_fields)
                                        for lease_id, lease_fields in extracted_fields.items()]

        return unstructured_data_leases

    def _get_original_citation(self, citation: str) -> str:
        """Extracts the original site ID from the citation string.

        Args:
            citation (str): Citation string in the format 'CITE{siteid}-{alias}'.

        Returns:
            str: Extracted site ID.
        """
        # Citation is in the format of CITE{siteid}-{alias}. Extract the site ID.
        # Validate the citation format in list-like string
        if citation.startswith("[") and citation.endswith("]"):
            try:
                citation_list = json.loads(citation)
                if isinstance(citation_list, list):
                    citation = citation_list[0]
            except Exception:
                raise ValueError(
                    "Invalid citation format. Expected format: '['CITE{siteid}-{alias}'].")

        if not citation.startswith("CITE") or "-" not in citation:
            raise ValueError("Invalid citation format. Expected format: 'CITE{siteid}-{alias}'.")

        # Extract and return the site ID
        site_id = citation.split('-')[0][4:]

        key = self.composite_key(site_id, self._config.lease_config_hash)

        if citation not in document_data_cache[key]['citation_mappings']:
            return None

        restored_citation = document_data_cache[key]['citation_mappings'][citation]

        return [restored_citation['source_document'], restored_citation['source_bounding_boxes']]

    def restore_structured_data(self) -> dict:
        """Retrieves structured data for the site.

        Returns:
            dict: A dictionary containing structured data for leases, with site IDs as keys
                and lists of LeaseAgreement objects as values.
        """
        if not self._site_id:
            raise ValueError("Site ID is not set. Cannot restore structured data.")

        cache_key = self.composite_key(self._site_id, self._config.lease_config_hash)
        data_str = document_data_cache[cache_key]["document_data_str"]
        data = json.loads(data_str)
        structured_data = data["leases_from_structured_data"]
        return structured_data

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
