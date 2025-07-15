import logging
from datetime import date
from pymongo.collection import Collection
from typing import Optional

from .container_client import ContainerClient, get_container_client
from .mongo_lock_manager import MongoLockManager
from models.extracted_collection_documents import ExtractedLeaseCollection, \
    ExtractedLeaseField, \
    ExtractedCollectionDocuments, \
    ExtractedCollectionInformationCollection
from models.data_collection_config import DataType, FieldDataCollectionConfig
from models.document_data_models import LeaseAgreementDocumentData
from models.ingestion_models import IngestDocumentType
from ._cosmos_client import CosmosClient
from models.environment_config import EnvironmentConfig
from utils.path_utils import build_adls_markdown_file_path, build_adls_pdf_file_path


def _build_document_id(collection_id: str, config_hash: str) -> str:
    """Builds the document ID for the collection document.

    Args:
        collection_id (str): The collection ID.
        config_hash (str): The configuration hash.

    Returns:
        str: The document ID.
    """
    return f"{collection_id}-{config_hash}"


class IngestionCollectionDocumentService(object):
    _collection_documents_collection: Collection
    _container_client: ContainerClient
    _mongo_lock_manager: MongoLockManager

    def __init__(
        self,
        collection_documents_collection: Collection,
        container_client: ContainerClient,
        mongo_lock_manager: MongoLockManager,
    ):
        """Initializes the IngestionConfigurationService with the given CosmosClient.

        Args:
            collection_documents_collection (Collection): The MongoDB collection to use for extracted documents.
            container_client (ContainerClient): The Azure ContainerClient instance.
            mongo_lock_manager (MongoLockManager): The MongoLockManager instance for managing locks.
        """
        self._container_client = container_client
        self._mongo_lock_manager = mongo_lock_manager
        self._collection_documents_collection = collection_documents_collection

    def ingest_analyzer_output(
        self,
        doc_type: IngestDocumentType,
        collection_id: str,
        lease_id: Optional[str],
        filename: str,
        date_of_document: date,
        data: dict,
        config: FieldDataCollectionConfig
    ):
        """Ingests the analyzer output into the database.

        Args:
            doc_type (IngestDocumentType): The type of the document being ingested.
            collection_id (str): The collection ID.
            lease_id (str): The lease ID.
            filename (str): The filename.
            date_of_document (date): The date of the document.
            data (dict): The analyzer output data.
            config (FieldDataCollectionConfig): The configuration object containing lease configuration hash.
        """
        field_list = self._extract_field_list(config)
        pdf_file_path = build_adls_pdf_file_path(
            doc_type,
            collection_id,
            filename,
            lease_id
        )
        markdown_file_path = build_adls_markdown_file_path(
            doc_type,
            collection_id,
            filename,
            lease_id
        )

        document_id = _build_document_id(collection_id, config.lease_config_hash)

        try:
            self._mongo_lock_manager.wait(document_id)
            existing_document = self._get_or_create_document(document_id, collection_id, config)
            try:
                lease = self._get_or_create_lease(existing_document, lease_id, pdf_file_path, markdown_file_path)
            except ValueError as e:
                logging.warning(f"Lease already exists: {e}")
                return

            self._update_markdowns_from_analyzer_output(data, markdown_file_path)

            self._update_fields_from_analyzer_output(lease,
                                                     data,
                                                     field_list,
                                                     date_of_document,
                                                     markdown_file_path,
                                                     pdf_file_path)
            self._upsert_document(existing_document)

            logging.info(
                f"Data ingested from analyzer output successfully for collection_id={collection_id}, lease_id={lease_id}, "
                f"lease_config_hash={config.lease_config_hash}"
            )
        except Exception as e:
            logging.error(f"Error occurred while ingesting data: {e}")
            raise
        finally:
            self._mongo_lock_manager.release_lock(document_id)

    def ingest_classifier_output(
        self,
        doc_type: IngestDocumentType,
        collection_id: str,
        lease_id: Optional[str],
        filename: str,
        date_of_document: date,
        data: dict,
        config: FieldDataCollectionConfig
    ):
        """Ingests the classifier output into the database.

        Args:
            doc_type (IngestDocumentType): The type of the document being ingested.
            collection_id (str): The collection ID.
            lease_id (str): The lease ID.
            filename (str): The filename.
            date_of_document (date): The date of the document.
            data (dict): The classifier output data.
            config (FieldDataCollectionConfig): The configuration object containing lease configuration hash.
        """
        field_list = self._extract_field_list(config)
        pdf_file_path = build_adls_pdf_file_path(
            doc_type,
            collection_id,
            filename,
            lease_id
        )
        markdown_file_path = build_adls_markdown_file_path(
            doc_type,
            collection_id,
            filename,
            lease_id
        )

        document_id = _build_document_id(collection_id, config.lease_config_hash)

        try:
            self._mongo_lock_manager.wait(document_id)
            existing_document = self._get_or_create_document(document_id, collection_id, config)
            try:
                lease = self._get_or_create_lease(existing_document, lease_id, pdf_file_path, markdown_file_path)
            except ValueError as e:
                logging.warning(f"Lease already exists: {e}")
                return

            self._update_markdowns_from_classifier_output(data, markdown_file_path)

            self._update_fields_from_classifier_output(lease,
                                                       data,
                                                       field_list,
                                                       date_of_document,
                                                       markdown_file_path,
                                                       pdf_file_path)

            self._upsert_document(existing_document)

            logging.info(
                f"Data ingested from classifier output successfully for collection_id={collection_id}, lease_id={lease_id}, "
                f"lease_config_hash={config.lease_config_hash}"
            )
        except Exception as e:
            logging.error(f"Error occurred while ingesting data: {e}")
            raise
        finally:
            self._mongo_lock_manager.release_lock(document_id)

    def clean_empty_document(
            self,
            collection_id: str,
            config: FieldDataCollectionConfig) -> bool:
        """Cleans up an empty document from the collection audit collection."""
        document_id = _build_document_id(collection_id, config.lease_config_hash)
        existing_document = self._collection_documents_collection.find_one(
            {"_id": document_id}
        )

        if not existing_document:
            return

        try:
            # Check if the document only contains the BaseMongoLockable fields
            ExtractedCollectionDocuments(**existing_document)
        except Exception:
            logging.info(f"Error parsing document. Deleting empty document with ID {document_id}")
            self._collection_documents_collection.delete_one({"_id": document_id})

    def is_document_ingested(
            self,
            doc_type: IngestDocumentType,
            collection_id: str,
            filename: str,
            config: FieldDataCollectionConfig,
            lease_id: Optional[str]) -> bool:
        """Checks if a lease document already exists.

        Args:
            collection_id (str): The collection ID.
            lease_id (str): The lease ID.
            filename (str): The filename.
            config (FieldDataCollectionConfig): The configuration object containing lease configuration hash.

        Returns:
            bool: True if the lease document exists, False otherwise.
        """
        document_id = _build_document_id(collection_id, config.lease_config_hash)
        existing_document = self._collection_documents_collection.find_one(
            {"_id": document_id}
        )

        if not existing_document:
            return False

        existing_document = ExtractedCollectionDocuments(**existing_document)
        lease = next((lease for lease in existing_document.information.leases if lease.lease_id == lease_id), None)

        if not lease:
            return False

        original_document_path = build_adls_pdf_file_path(
            doc_type,
            collection_id,
            filename,
            lease_id,
        )

        if original_document_path not in lease.original_documents:
            return False

        return True

    def _extract_field_list(self, config: FieldDataCollectionConfig):
        field_list = []
        for collection_row in config.collection_rows:
            if collection_row.data_type is not DataType.LEASE_AGREEMENT:
                continue

            for field_schema in collection_row.field_schema:
                field_list.append(field_schema.name)

        return field_list

    def _get_or_create_document(
        self,
        document_id: str,
        collection_id: str,
        config: FieldDataCollectionConfig,
    ):
        existing_document = self._collection_documents_collection.find_one(
            {"_id": document_id}
        )

        if not existing_document or existing_document.get("collection_id") is None:
            document = ExtractedCollectionDocuments(
                collection_id=collection_id,
                config_id=config.id,
                lease_config_hash=config.lease_config_hash,
                information=ExtractedCollectionInformationCollection(leases=[]),
                **(existing_document or {})  # Include MongoLock data
            )
        else:
            document = ExtractedCollectionDocuments(**existing_document)
            document.config_id = config.id

        document.id = document_id

        return document

    def _get_or_create_lease(
        self,
        existing_document: ExtractedCollectionDocuments,
        lease_id: str,
        pdf_path: str,
        markdown_path: str
    ):
        lease = next((lease for lease in existing_document.information.leases if lease.lease_id == lease_id), None)
        if lease is None:
            lease = ExtractedLeaseCollection(
                lease_id=lease_id,
                original_documents=[
                ],
                markdowns=[
                ],
                fields={}
            )
            existing_document.information.leases.append(lease)

        if pdf_path not in lease.original_documents:
            lease.original_documents.append(pdf_path)
        else:
            logging.warning(
                f"PDF file already ingested for lease_id={lease_id} and collection_id={existing_document.collection_id} "
                f"with hash={existing_document.lease_config_hash}."
            )

        if markdown_path not in lease.markdowns:
            lease.markdowns.append(markdown_path)
        else:
            logging.warning(
                f"Markdown file already ingested for lease_id={lease_id} and collection_id={existing_document.collection_id} "
                f"with hash={existing_document.lease_config_hash}."
            )

        return lease

    def _process_extracted_field(
        self,
        lease: ExtractedLeaseCollection,
        field_name: str,
        field_value: dict,
        field_list: list,
        date_of_document: date,
        markdown_path: str,
        pdf_path: str,
        category: str = None,
        subdocument_start_page: str = None,
        subdocument_end_page: str = None
    ) -> bool:
        """Processes a single extracted field and adds it to the lease if valid.

        Args:
            lease (ExtractedLeaseCollection): The lease to add the field to.
            field_name (str): The name of the field.
            field_value (dict): The field value data.
            field_list (list): List of allowed field names.
            date_of_document (date): The date of the document.
            markdown_path (str): Path to the markdown file.
            pdf_path (str): Path to the PDF file.
            category (str, optional): Document category for classifier output.
            subdocument_start_page (str, optional): Start page for classifier output.
            subdocument_end_page (str, optional): End page for classifier output.

        Returns:
            bool: True if the field was processed, False if it was skipped.
        """
        if field_name not in field_list:
            logging.info(f"Skipping field '{field_name}'. Field is not part of the configuration.")
            return False

        if (
            'valueString' not in field_value
            and 'valueNumber' not in field_value
            and 'valueArray' not in field_value
            and 'valueObject' not in field_value
            and 'valueInteger' not in field_value
            and 'valueDate' not in field_value
            and 'valueTime' not in field_value
        ):
            logging.info(f"Skipping field '{field_name}'. Field values could not be extracted. {field_value}")
            return False

        # Build the field data
        field_data = {
            **field_value,
            'date_of_document': date_of_document,
            'markdown': markdown_path,
            'document': pdf_path
        }

        # Add classifier-specific fields if provided
        if category is not None:
            field_data['category'] = category
        if subdocument_start_page is not None:
            field_data['subdocument_start_page'] = subdocument_start_page
        if subdocument_end_page is not None:
            field_data['subdocument_end_page'] = subdocument_end_page

        # Append to the list of ExtractedLeaseField if the field already exists
        if field_name in lease.fields:
            lease.fields[field_name].append(ExtractedLeaseField(**field_data))
        else:
            # Initialize the field with a list containing the new ExtractedLeaseField
            lease.fields[field_name] = [ExtractedLeaseField(**field_data)]

        return True

    def _update_markdowns_from_analyzer_output(self, data: dict, path: str):
        if self._container_client.file_exists(path):
            logging.info(f"Markdown file already exists at {path}.")
            return
        for content in data['result']['contents']:
            markdown = content['markdown']
            self._container_client.upload_document(markdown, path)

    def _update_fields_from_analyzer_output(
        self,
        lease: ExtractedLeaseCollection,
        data: dict,
        field_list: list,
        date_of_document: date,
        markdown_path: str,
        pdf_path: str
    ):
        for field_name, field_value in data['result']['contents'][0]['fields'].items():
            self._process_extracted_field(
                lease,
                field_name,
                field_value,
                field_list,
                date_of_document,
                markdown_path,
                pdf_path
            )

    def _update_markdowns_from_classifier_output(self, data: dict, path: str):
        if self._container_client.file_exists(path):
            logging.info(f"Markdown file already exists at {path}.")
            return

        # Get all returned markdown content from the classifier output
        # We might have multiple returned documents, so iterate over all of them
        # to retrieve markdowns and concatenate them
        full_markdown_content = ''

        for content in data['result']['contents']:
            if 'markdown' in content:
                full_markdown_content += content['markdown'] + ' '

        self._container_client.upload_document(full_markdown_content, path)

    def _update_fields_from_classifier_output(
        self,
        lease: ExtractedLeaseCollection,
        data: dict,
        field_list: list,
        date_of_document: date,
        markdown_path: str,
        pdf_path: str
    ):
        # Iterate over all returned documents from classifier output
        for document_content in data['result']['contents']:

            # Check if the document has analyzer results - if not, continue
            if 'fields' not in document_content:
                continue

            # Iterate over all fields returned by the analyzer for that document
            for field_name, field_value in document_content['fields'].items():
                self._process_extracted_field(
                    lease,
                    field_name,
                    field_value,
                    field_list,
                    date_of_document,
                    markdown_path,
                    pdf_path,
                    category=document_content['category'],
                    subdocument_start_page=document_content['startPageNumber'],
                    subdocument_end_page=document_content['endPageNumber']
                )

    def _upsert_document(
        self,
        existing_document: ExtractedCollectionDocuments
    ):
        self._collection_documents_collection.update_one(
            {"_id": existing_document.id},
            {"$set": existing_document.model_dump(by_alias=True, mode='json', exclude_defaults=True)},
            upsert=True
        )

    def _get_all_extracted_fields_from_collection_doc(self, collection_id: str, config: FieldDataCollectionConfig) -> dict:
        """Gets all extracted fields from an existing collection document.

        Args:
            collection_id (str): The ID of the collection being queried.
            config (FieldDataCollectionConfig): The configuration object containing lease configuration hash.

        Returns:
            dict: A dictionary keyed by lease ID. Each entry in the top-level dictionary is another
                  dictionary of the extracted key-value pairs from each lease document, keyed by field name.
        """
        # Dict to store all fields from leases in this collection
        all_lease_fields_dict = {}

        # Query Cosmos for collection document
        logging.info(f"Querying CosmosDB for collection ID {collection_id} and Lease Config Hash {config.lease_config_hash}")
        existing_document = self._collection_documents_collection.find_one(
            {"_id": _build_document_id(collection_id.upper(), config.lease_config_hash)}
        )
        if not existing_document or existing_document.get("collection_id") is None:
            logging.warning(
                f"data for collection {collection_id} and lease config hash {config.lease_config_hash} does not exist."
            )
            return all_lease_fields_dict
        existing_document = ExtractedCollectionDocuments(**existing_document)

        # Iterate over all leases in the collection document
        for lease in existing_document.information.leases:
            lease_key = lease.lease_id
            if lease_key in all_lease_fields_dict:
                logging.error(f"A lease with ID {lease_key} has already been processed - skipping...")
                continue

            lease_field_dict = {}
            # Get stringified values of each element

            for field_name, field_values in lease.fields.items():
                lease_agreement_data: list[dict] = []
                for field_value in field_values:
                    lease_agreement_data.append(
                        LeaseAgreementDocumentData(**field_value.model_dump())
                    )

                lease_field_dict[field_name] = lease_agreement_data

            # Update the top-level dictionary with the lease fields
            all_lease_fields_dict[lease_key] = lease_field_dict

        return all_lease_fields_dict

    @classmethod
    def from_environment_config(cls, environment_config: EnvironmentConfig):
        """Creates a ConfigManagementService instance from a connection string.

        Args:
            environment_config (EnvironmentConfig): The environment configuration.

        Returns:
            ConfigManagementService: The ConfigManagementService instance.
        """
        cosmos_client = CosmosClient(environment_config.cosmosdb.endpoint.value)
        container_client = get_container_client(environment_config)
        collection_documents_collection = cosmos_client.get_collection(
            environment_config.cosmosdb.db_name.value,
            environment_config.cosmosdb.document_collection_name.value
        )
        mongo_lock_manager = MongoLockManager(
            collection_documents_collection,
        )
        return cls(
            collection_documents_collection=collection_documents_collection,
            container_client=container_client,
            mongo_lock_manager=mongo_lock_manager
        )
