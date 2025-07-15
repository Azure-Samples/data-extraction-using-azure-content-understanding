import unittest
from unittest.mock import patch, MagicMock
from datetime import date

from services.ingest_lease_documents_service import IngestionCollectionDocumentService
from models.data_collection_config import (
    FieldDataCollectionConfig,
    LeaseAgreementCollectionRow,
    FieldSchema,
    FieldMappingType,
    ClassifierConfig
)
from models.extracted_collection_documents import (
    ExtractedCollectionDocuments,
    ExtractedCollectionInformationCollection,
    ExtractedLeaseCollection,
    ExtractedLeaseField,
    ExtractedLeaseFieldType
)
from models.document_data_models import LeaseAgreementDocumentData
from models.ingestion_models import IngestDocumentType


class TestIngestionCollectionDocumentServiceIngestAnalyzerOutput(unittest.TestCase):
    def setUp(self):
        # Make sure the mock has a 'cosmosdb' attribute with nested fields
        self.mock_container_client = MagicMock()
        self.mock_collection_documents_collection = MagicMock()
        self.mock_mongo_lock_manager = MagicMock()

        self.service = IngestionCollectionDocumentService(
            collection_documents_collection=self.mock_collection_documents_collection,
            container_client=self.mock_container_client,
            mongo_lock_manager=self.mock_mongo_lock_manager,
        )

        self.config = FieldDataCollectionConfig(
            name="test-config",
            version="1.0",
            lease_config_hash="fake_hash",
            prompt="Test prompt",
            collection_rows=[
                LeaseAgreementCollectionRow(
                    analyzer_id="analyzer_id",
                    field_schema=[
                        FieldSchema(
                            name="field1",
                            type=FieldMappingType.STRING,
                            description="Field 1 description",
                        ),
                        FieldSchema(
                            name="field2",
                            type=FieldMappingType.INTEGER,
                            description="Field 2 description",
                        ),
                    ]
                )
            ]
        )
        self.config.id = "config-id"

    @patch("services.ingest_lease_documents_service.logging")
    def test_ingest_analyzer_output_success(self, mock_logging):
        data = {
            "result": {
                "contents": [
                    {
                        "fields": {
                            "field1": {
                                "valueString": "test_value",
                                "confidence": 0.95,
                                "type": "string",
                            },
                            "field2": {
                                "valueNumber": 123,
                                "confidence": 0.90,
                                "type": "number",
                            }
                        },
                        "markdown": "some_markdown"
                    }
                ]
            }
        }
        self.mock_collection_documents_collection.find_one.return_value = None
        self.mock_container_client.file_exists.return_value = False

        self.service.ingest_analyzer_output(
            doc_type=IngestDocumentType.COLLECTION,
            market="market 1",
            collection_id="test_collection",
            lease_id="test_lease",
            filename="test_file.pdf",
            date_of_document=date(2023, 1, 1),
            data=data,
            config=self.config
        )

        self.mock_collection_documents_collection.find_one.assert_called_once_with(
            {"_id": "test_collection-fake_hash"}
        )
        self.mock_mongo_lock_manager.wait.assert_called_once_with(
            "test_collection-fake_hash"
        )
        self.mock_mongo_lock_manager.release_lock.assert_called_once_with(
            "test_collection-fake_hash"
        )
        self.mock_container_client.upload_document.assert_called_once_with(
            "some_markdown",
            "Collections/market 1/test_collection/test_lease/test_file.md"
        )
        mock_logging.info.assert_called_with(
            "Data ingested from analyzer output successfully for collection_id=test_collection, "
            "lease_id=test_lease, lease_config_hash=fake_hash"
        )
        self.mock_collection_documents_collection.update_one.assert_called_once_with(
            {"_id": "test_collection-fake_hash"},
            {
                "$set":
                {
                    "_id": "test_collection-fake_hash",
                    "collection_id": "test_collection",
                    "config_id": "config-id",
                    "lease_config_hash": "fake_hash",
                    "information": {
                        "leases": [
                            {
                                "lease_id": "test_lease",
                                "original_documents": [
                                    "Collections/market 1/test_collection/test_lease/test_file.pdf"
                                ],
                                "markdowns": [
                                    "Collections/market 1/test_collection/test_lease/test_file.md"
                                ],
                                "fields": {
                                    "field1": [
                                        {
                                            "type": "string",
                                            "valueString": "test_value",
                                            "confidence": 0.95,
                                            "date_of_document": "2023-01-01",
                                            "markdown": "Collections/market 1/test_collection/test_lease/test_file.md",
                                            "document": "Collections/market 1/test_collection/test_lease/test_file.pdf"
                                        }
                                    ],
                                    "field2": [
                                        {
                                            "type": "number",
                                            "valueNumber": 123.0,
                                            "confidence": 0.9,
                                            "date_of_document": "2023-01-01",
                                            "markdown": "Collections/market 1/test_collection/test_lease/test_file.md",
                                            "document": "Collections/market 1/test_collection/test_lease/test_file.pdf"
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            },
            upsert=True
        )

    @patch("services.ingest_lease_documents_service.logging")
    def test_ingest_analyzer_output_exception(self, mock_logging):
        data = {}
        self.mock_collection_documents_collection.find_one.side_effect = Exception("DB error")

        # pytest catch the error and log it
        with self.assertRaises(Exception) as ex:
            self.service.ingest_analyzer_output(
                doc_type=IngestDocumentType.COLLECTION,
                market="market 1",
                collection_id="bad_collection",
                lease_id="lease",
                filename="file.pdf",
                date_of_document=date(2023, 1, 1),
                data=data,
                config=self.config
            )

            mock_logging.error.assert_called_with("Error occurred while ingesting data: DB error")
            self.assertEqual(str(ex.exception), "DB error")

    @patch("services.ingest_lease_documents_service.logging")
    def test_ingest_analyzer_output_with_existing_document(self, mock_logging):
        data = {
            "result": {
                "contents": [
                    {
                        "fields": {
                            "fieldA": {"valueString": "string_value"}
                        }
                    }
                ]
            }
        }
        existing_doc = ExtractedCollectionDocuments(
            collection_id="test_collection",
            config_id="old_config_id",
            lease_config_hash="",
            information=ExtractedCollectionInformationCollection(leases=[])
        )
        self.mock_collection_documents_collection.find_one.return_value = existing_doc.model_dump()

        self.service.ingest_analyzer_output(
            doc_type=IngestDocumentType.COLLECTION,
            market="market 1",
            collection_id="test_collection",
            lease_id="abc_lease",
            filename="abc.pdf",
            date_of_document=date(2023, 1, 1),
            data=data,
            config=self.config
        )

        self.assertEqual(self.mock_collection_documents_collection.find_one.call_count, 1)
        mock_logging.info.assert_called_with(
            "Data ingested from analyzer output successfully for collection_id=test_collection, "
            "lease_id=abc_lease, lease_config_hash=fake_hash"
        )

    @patch("services.ingest_lease_documents_service.logging")
    def test_ingest_analyzer_output_field_not_in_config(self, mock_logging):
        # FieldDataCollectionConfig has empty collection_rows, so no fields are valid
        data = {
            "result": {
                "contents": [
                    {
                        "fields": {
                            "unlisted_field": {"valueString": "should_skip"}
                        }
                    }
                ]
            }
        }
        self.mock_collection_documents_collection.find_one.return_value = None

        self.service.ingest_analyzer_output(
            doc_type=IngestDocumentType.COLLECTION,
            market="market 1",
            collection_id="test_collection",
            lease_id="test_lease",
            filename="test_file.pdf",
            date_of_document=date(2023, 1, 1),
            data=data,
            config=self.config
        )

        # Verify that the field was skipped with appropriate logging
        mock_logging.info.assert_any_call(
            "Skipping field 'unlisted_field'. Field is not part of the configuration."
        )


class TestIngestionCollectionDocumentServiceCleanEmptyDocument(unittest.TestCase):
    def setUp(self):
        self.mock_container_client = MagicMock()
        self.mock_collection_documents_collection = MagicMock()
        self.mock_mongo_lock_manager = MagicMock()

        self.service = IngestionCollectionDocumentService(
            collection_documents_collection=self.mock_collection_documents_collection,
            container_client=self.mock_container_client,
            mongo_lock_manager=self.mock_mongo_lock_manager,
        )

        self.config = FieldDataCollectionConfig(
            name="test-config",
            version="1.0",
            lease_config_hash="fake_hash",
            prompt="Test prompt",
            collection_rows=[]
        )
        self.config.id = "config-id"

    def test_clean_empty_document_deletes_empty_document(self):
        document_id = "test_collection-fake_hash"
        self.mock_collection_documents_collection.find_one.return_value = {"_id": document_id}

        with patch("services.ingest_lease_documents_service.ExtractedCollectionDocuments", side_effect=Exception):
            self.service.clean_empty_document(collection_id="test_collection", config=self.config)

        self.mock_collection_documents_collection.find_one.assert_called_once_with({"_id": document_id})
        self.mock_collection_documents_collection.delete_one.assert_called_once_with({"_id": document_id})

    def test_clean_empty_document_no_action_for_valid_document(self):
        document_id = "test_collection-fake_hash"
        valid_document = {"_id": document_id, "collection_id": "test_collection"}
        self.mock_collection_documents_collection.find_one.return_value = valid_document

        with patch("services.ingest_lease_documents_service.ExtractedCollectionDocuments"):
            self.service.clean_empty_document(collection_id="test_collection", config=self.config)

        self.mock_collection_documents_collection.find_one.assert_called_once_with({"_id": document_id})
        self.mock_collection_documents_collection.delete_one.assert_not_called()


class TestIngestionCollectionDocumentServiceIsLeaseDocumentIngested(unittest.TestCase):
    def setUp(self):
        self.mock_container_client = MagicMock()
        self.mock_collection_documents_collection = MagicMock()
        self.mock_mongo_lock_manager = MagicMock()

        self.service = IngestionCollectionDocumentService(
            collection_documents_collection=self.mock_collection_documents_collection,
            container_client=self.mock_container_client,
            mongo_lock_manager=self.mock_mongo_lock_manager,
        )

        self.config = FieldDataCollectionConfig(
            name="test-config",
            version="1.0",
            lease_config_hash="fake_hash",
            prompt="Test prompt",
            collection_rows=[]
        )
        self.config.id = "config-id"

    def test_is_lease_document_ingested_returns_true(self):
        document_id = "test_collection-fake_hash"
        existing_document = ExtractedCollectionDocuments(
            collection_id="test_collection",
            config_id="config-id",
            lease_config_hash="fake_hash",
            information=ExtractedCollectionInformationCollection(
                leases=[
                    {
                        "lease_id": "test_lease",
                        "original_documents": ["Collections/market/test_collection/test_lease/test_file.pdf"],
                        "markdowns": ["Collections/market/test_collection/test_lease/test_file.md"],
                        "fields": {
                            "field1": [
                                {
                                    "type": "string",
                                    "valueString": "test_value",
                                    "spans": [],
                                    "confidence": 0.95,
                                    "source": None,
                                    "date_of_document": "2023-01-01"
                                }
                            ]
                        }
                    }
                ]
            )
        )
        self.mock_collection_documents_collection.find_one.return_value = existing_document.model_dump()

        result = self.service.is_lease_document_ingested(
            doc_type=IngestDocumentType.COLLECTION,
            collection_id="test_collection",
            filename="test_file.pdf",
            config=self.config,
            market="market",
            lease_id="test_lease"
        )

        self.assertTrue(result)
        self.mock_collection_documents_collection.find_one.assert_called_once_with({"_id": document_id})

    def test_is_lease_document_ingested_returns_false_for_missing_site_document(self):
        self.mock_collection_documents_collection.find_one.return_value = None

        result = self.service.is_lease_document_ingested(
            doc_type=IngestDocumentType.COLLECTION,
            collection_id="test_collection",
            filename="test_file.pdf",
            config=self.config,
            market="market",
            lease_id="test_lease"
        )

        self.assertFalse(result)
        self.mock_collection_documents_collection.find_one.assert_called_once_with({"_id": "test_collection-fake_hash"})

    def test_is_lease_document_ingested_returns_false_for_missing_lease(self):
        existing_document = ExtractedCollectionDocuments(
            collection_id="test_collection",
            config_id="config-id",
            lease_config_hash="fake_hash",
            information=ExtractedCollectionInformationCollection(leases=[])
        )
        self.mock_collection_documents_collection.find_one.return_value = existing_document.model_dump()

        result = self.service.is_lease_document_ingested(
            doc_type=IngestDocumentType.COLLECTION,
            collection_id="test_collection",
            filename="test_file.pdf",
            config=self.config,
            market="market",
            lease_id="test_lease"
        )

        self.assertFalse(result)

    def test_is_lease_document_ingested_returns_false_for_missing_file_path(self):
        existing_document = ExtractedCollectionDocuments(
            collection_id="test_collection",
            config_id="config-id",
            lease_config_hash="fake_hash",
            information=ExtractedCollectionInformationCollection(
                leases=[
                    {
                        "lease_id": "test_lease",
                        "original_documents": ["Collections/market/test_collection/test_lease/other_file.pdf"],
                        "markdowns": ["Collections/market/test_collection/test_lease/other_file.md"],
                        "fields": {
                            "field1": [
                                {
                                    "type": "string",
                                    "valueString": "test_value",
                                    "spans": [],
                                    "confidence": 0.95,
                                    "source": None,
                                    "date_of_document": "2023-01-01"
                                }
                            ]
                        }
                    }
                ]
            )
        )
        self.mock_collection_documents_collection.find_one.return_value = existing_document.model_dump()

        result = self.service.is_lease_document_ingested(
            doc_type=IngestDocumentType.COLLECTION,
            collection_id="test_collection",
            filename="test_file.pdf",
            config=self.config,
            market="market",
            lease_id="test_lease"
        )

        self.assertFalse(result)


class TestIngestionCollectionDocumentServiceIngestClassifierOutput(unittest.TestCase):
    def setUp(self):
        # Make sure the mock has a 'cosmosdb' attribute with nested fields
        self.mock_container_client = MagicMock()
        self.mock_collection_documents_collection = MagicMock()
        self.mock_mongo_lock_manager = MagicMock()

        self.service = IngestionCollectionDocumentService(
            collection_documents_collection=self.mock_collection_documents_collection,
            container_client=self.mock_container_client,
            mongo_lock_manager=self.mock_mongo_lock_manager,
        )

        self.config = FieldDataCollectionConfig(
            name="test-config",
            version="1.0",
            lease_config_hash="fake_hash",
            prompt="Test prompt",
            collection_rows=[
                LeaseAgreementCollectionRow(
                    analyzer_id="analyzer_id",
                    field_schema=[
                        FieldSchema(
                            name="field1",
                            type=FieldMappingType.STRING,
                            description="Field 1 description",
                        ),
                        FieldSchema(
                            name="field2",
                            type=FieldMappingType.INTEGER,
                            description="Field 2 description",
                        )
                    ],
                    classifier=ClassifierConfig(
                        enabled=True,
                        classifier_id="classifier_id"
                    )
                )
            ]
        )
        self.config.id = "config-id"

    @patch("services.ingest_lease_documents_service.logging")
    def test_ingest_classifier_output_success(self, mock_logging):
        data = {
            "result": {
                "contents": [
                    {
                        "category": "lease_agreement",
                        "startPageNumber": 1,
                        "endPageNumber": 5,
                        "fields": {
                            "field1": {
                                "valueString": "test_value",
                                "confidence": 0.95,
                                "type": "string",
                            },
                            "field2": {
                                "valueNumber": 123,
                                "confidence": 0.90,
                                "type": "number",
                            }
                        },
                        "markdown": "some_markdown_content"
                    },
                    {
                        "category": "amendment",
                        "startPageNumber": 6,
                        "endPageNumber": 10,
                        "fields": {
                            "field1": {
                                "valueString": "another_value",
                                "confidence": 0.88,
                                "type": "string",
                            }
                        },
                        "markdown": "more_markdown_content"
                    }
                ]
            }
        }
        self.mock_collection_documents_collection.find_one.return_value = None
        self.mock_container_client.file_exists.return_value = False

        self.service.ingest_classifier_output(
            doc_type=IngestDocumentType.COLLECTION,
            market="market 1",
            collection_id="test_collection",
            lease_id="test_lease",
            filename="test_file.pdf",
            date_of_document=date(2023, 1, 1),
            data=data,
            config=self.config
        )

        self.mock_collection_documents_collection.find_one.assert_called_once_with(
            {"_id": "test_collection-fake_hash"}
        )
        self.mock_mongo_lock_manager.wait.assert_called_once_with(
            "test_collection-fake_hash"
        )
        self.mock_mongo_lock_manager.release_lock.assert_called_once_with(
            "test_collection-fake_hash"
        )
        self.mock_container_client.upload_document.assert_called_once_with(
            "some_markdown_content more_markdown_content ",
            "Collections/market 1/test_collection/test_lease/test_file.md"
        )
        mock_logging.info.assert_called_with(
            "Data ingested from classifier output successfully for collection_id=test_collection, "
            "lease_id=test_lease, lease_config_hash=fake_hash"
        )
        self.mock_collection_documents_collection.update_one.assert_called_once_with(
            {"_id": "test_collection-fake_hash"},
            {
                "$set":
                {
                    "_id": "test_collection-fake_hash",
                    "collection_id": "test_collection",
                    "config_id": "config-id",
                    "lease_config_hash": "fake_hash",
                    "information": {
                        "leases": [
                            {
                                "lease_id": "test_lease",
                                "original_documents": [
                                    "Collections/market 1/test_collection/test_lease/test_file.pdf"
                                ],
                                "markdowns": [
                                    "Collections/market 1/test_collection/test_lease/test_file.md"
                                ],
                                "fields": {
                                    "field1": [
                                        {
                                            "type": "string",
                                            "valueString": "test_value",
                                            "confidence": 0.95,
                                            "date_of_document": "2023-01-01",
                                            "markdown": "Collections/market 1/test_collection/test_lease/test_file.md",
                                            "document": "Collections/market 1/test_collection/test_lease/test_file.pdf",
                                            "category": "lease_agreement",
                                            "subdocument_start_page": 1,
                                            "subdocument_end_page": 5
                                        },
                                        {
                                            "type": "string",
                                            "valueString": "another_value",
                                            "confidence": 0.88,
                                            "date_of_document": "2023-01-01",
                                            "markdown": "Collections/market 1/test_collection/test_lease/test_file.md",
                                            "document": "Collections/market 1/test_collection/test_lease/test_file.pdf",
                                            "category": "amendment",
                                            "subdocument_start_page": 6,
                                            "subdocument_end_page": 10
                                        }
                                    ],
                                    "field2": [
                                        {
                                            "type": "number",
                                            "valueNumber": 123.0,
                                            "confidence": 0.9,
                                            "date_of_document": "2023-01-01",
                                            "markdown": "Collections/market 1/test_collection/test_lease/test_file.md",
                                            "document": "Collections/market 1/test_collection/test_lease/test_file.pdf",
                                            "category": "lease_agreement",
                                            "subdocument_start_page": 1,
                                            "subdocument_end_page": 5
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            },
            upsert=True
        )

    @patch("services.ingest_lease_documents_service.logging")
    def test_ingest_classifier_output_exception(self, mock_logging):
        data = {}
        self.mock_collection_documents_collection.find_one.side_effect = Exception("DB error")

        # pytest catch the error and log it
        with self.assertRaises(Exception) as ex:
            self.service.ingest_classifier_output(
                doc_type=IngestDocumentType.COLLECTION,
                market="market 1",
                collection_id="bad_collection",
                lease_id="lease",
                filename="file.pdf",
                date_of_document=date(2023, 1, 1),
                data=data,
                config=self.config
            )

            mock_logging.error.assert_called_with("Error occurred while ingesting data: DB error")
            self.assertEqual(str(ex.exception), "DB error")

    @patch("services.ingest_lease_documents_service.logging")
    def test_ingest_classifier_output_with_existing_document(self, mock_logging):
        data = {
            "result": {
                "contents": [
                    {
                        "category": "lease_agreement",
                        "startPageNumber": 1,
                        "endPageNumber": 3,
                        "fields": {
                            "fieldA": {"valueString": "string_value"}
                        },
                        "markdown": "markdown_content"
                    }
                ]
            }
        }
        existing_doc = ExtractedCollectionDocuments(
            collection_id="test_collection",
            config_id="old_config_id",
            lease_config_hash="",
            information=ExtractedCollectionInformationCollection(leases=[])
        )
        self.mock_collection_documents_collection.find_one.return_value = existing_doc.model_dump()

        self.service.ingest_classifier_output(
            doc_type=IngestDocumentType.COLLECTION,
            market="market 1",
            collection_id="test_collection",
            lease_id="abc_lease",
            filename="abc.pdf",
            date_of_document=date(2023, 1, 1),
            data=data,
            config=self.config
        )

        self.assertEqual(self.mock_collection_documents_collection.find_one.call_count, 1)
        mock_logging.info.assert_called_with(
            "Data ingested from classifier output successfully for collection_id=test_collection, "
            "lease_id=abc_lease, lease_config_hash=fake_hash"
        )

    @patch("services.ingest_lease_documents_service.logging")
    def test_ingest_classifier_output_field_not_in_config(self, mock_logging):
        data = {
            "result": {
                "contents": [
                    {
                        "category": "lease_agreement",
                        "startPageNumber": 1,
                        "endPageNumber": 2,
                        "fields": {
                            "unlisted_field": {"valueString": "should_skip"}
                        },
                        "markdown": "markdown_content"
                    }
                ]
            }
        }
        self.mock_collection_documents_collection.find_one.return_value = None
        self.mock_container_client.file_exists.return_value = False

        self.service.ingest_classifier_output(
            doc_type=IngestDocumentType.COLLECTION,
            market="market 1",
            collection_id="test_collection",
            lease_id="test_lease",
            filename="test_file.pdf",
            date_of_document=date(2023, 1, 1),
            data=data,
            config=self.config
        )

        # Verify that the field was skipped with appropriate logging
        mock_logging.info.assert_any_call(
            "Skipping field 'unlisted_field'. Field is not part of the configuration."
        )

        # Verify successful completion logging
        mock_logging.info.assert_any_call(
            "Data ingested from classifier output successfully for collection_id=test_collection, "
            "lease_id=test_lease, lease_config_hash=fake_hash"
        )
        self.mock_container_client = MagicMock()
        self.mock_collection_documents_collection = MagicMock()
        self.mock_mongo_lock_manager = MagicMock()

        self.service = IngestionCollectionDocumentService(
            collection_documents_collection=self.mock_collection_documents_collection,
            container_client=self.mock_container_client,
            mongo_lock_manager=self.mock_mongo_lock_manager,
        )

        self.config = FieldDataCollectionConfig(
            name="test-config",
            version="1.0",
            lease_config_hash="test_hash",
            prompt="Test prompt",
            collection_rows=[
                LeaseAgreementCollectionRow(
                    analyzer_id="analyzer_id",
                    field_schema=[
                        FieldSchema(
                            name="field1",
                            type=FieldMappingType.STRING,
                            description="Field 1 description",
                        ),
                        FieldSchema(
                            name="field2",
                            type=FieldMappingType.INTEGER,
                            description="Field 2 description",
                        ),
                    ]
                )
            ]
        )
        self.config.id = "config-id"


class TestIngestionCollectionDocumentServiceGetAllExtractedFields(unittest.TestCase):
    def setUp(self):
        self.mock_container_client = MagicMock()
        self.mock_collection_documents_collection = MagicMock()
        self.mock_mongo_lock_manager = MagicMock()

        self.service = IngestionCollectionDocumentService(
            collection_documents_collection=self.mock_collection_documents_collection,
            container_client=self.mock_container_client,
            mongo_lock_manager=self.mock_mongo_lock_manager,
        )

        self.config = FieldDataCollectionConfig(
            name="test-config",
            version="1.0",
            lease_config_hash="test_hash",
            prompt="Test prompt",
            collection_rows=[
                LeaseAgreementCollectionRow(
                    analyzer_id="analyzer_id",
                    field_schema=[
                        FieldSchema(
                            name="field1",
                            type=FieldMappingType.STRING,
                            description="Field 1 description",
                        ),
                        FieldSchema(
                            name="field2",
                            type=FieldMappingType.INTEGER,
                            description="Field 2 description",
                        ),
                    ]
                )
            ]
        )
        self.config.id = "config-id"

    @patch("services.ingest_lease_documents_service.logging")
    def test_get_all_extracted_fields_success_with_multiple_leases(self, mock_logging):
        """Test successful extraction with multiple leases and fields."""
        # Create test data with multiple leases
        lease1_fields = {
            "field1": [
                ExtractedLeaseField(
                    type=ExtractedLeaseFieldType.STRING,
                    valueString="lease1_value1",
                    confidence=0.9,
                    date_of_document=date(2023, 1, 1),
                    document="lease1_LSE_doc.pdf"
                ),
                ExtractedLeaseField(
                    type=ExtractedLeaseFieldType.STRING,
                    valueString="lease1_value1_amendment",
                    confidence=0.8,
                    date_of_document=date(2023, 6, 1),
                    document="lease1_AMD_doc.pdf"
                )
            ],
            "field2": [
                ExtractedLeaseField(
                    type=ExtractedLeaseFieldType.INTEGER,
                    valueInteger=100,
                    confidence=0.95,
                    date_of_document=date(2023, 1, 1),
                    document="lease1_LSE_doc.pdf"
                )
            ]
        }

        lease2_fields = {
            "field1": [
                ExtractedLeaseField(
                    type=ExtractedLeaseFieldType.STRING,
                    valueString="lease2_value1",
                    confidence=0.85,
                    date_of_document=date(2023, 2, 1),
                    document="lease2_LSE_doc.pdf"
                )
            ]
        }

        existing_document = ExtractedCollectionDocuments(
            collection_id="test_collection",
            config_id="config-id",
            lease_config_hash="test_hash",
            information=ExtractedCollectionInformationCollection(
                leases=[
                    ExtractedLeaseCollection(
                        lease_id="lease1",
                        original_documents=["lease1_LSE_doc.pdf", "lease1_AMD_doc.pdf"],
                        markdowns=["lease1_LSE_doc.md", "lease1_AMD_doc.md"],
                        fields=lease1_fields
                    ),
                    ExtractedLeaseCollection(
                        lease_id="lease2",
                        original_documents=["lease2_LSE_doc.pdf"],
                        markdowns=["lease2_LSE_doc.md"],
                        fields=lease2_fields
                    )
                ]
            )
        )

        self.mock_collection_documents_collection.find_one.return_value = existing_document.model_dump()

        result = self.service._get_all_extracted_fields_from_collection_doc("test_collection", self.config)

        # Verify the structure and content
        self.assertEqual(len(result), 2)  # Two leases
        self.assertIn("lease1", result)
        self.assertIn("lease2", result)

        # Check lease1 fields
        lease1_result = result["lease1"]
        self.assertIn("field1", lease1_result)
        self.assertIn("field2", lease1_result)

        # field1 should have 1 lease agreement data (AMD) + 1 max field value (LSE)
        self.assertEqual(len(lease1_result["field1"]), 2)

        # field2 should have 1 max field value (LSE)
        self.assertEqual(len(lease1_result["field2"]), 1)

        # Check lease2 fields
        lease2_result = result["lease2"]
        self.assertIn("field1", lease2_result)
        self.assertEqual(len(lease2_result["field1"]), 1)  # 1 max field value

        # Verify logging calls
        mock_logging.info.assert_called_with(
            "Querying CosmosDB for collection ID test_collection and Lease Config Hash test_hash"
        )

    @patch("services.ingest_lease_documents_service.logging")
    def test_get_all_extracted_fields_no_document_found(self, mock_logging):
        """Test when no document is found in the database."""
        self.mock_collection_documents_collection.find_one.return_value = None

        result = self.service._get_all_extracted_fields_from_collection_doc("nonexistent_collection", self.config)

        self.assertEqual(result, {})
        mock_logging.warning.assert_called_with(
            "data for collection nonexistent_collection and lease config hash test_hash does not exist."
        )

    @patch("services.ingest_lease_documents_service.logging")
    def test_get_all_extracted_fields_with_lease_documents(self, mock_logging):
        """Test extraction with fields."""
        # Create test data where some fields are from lease documents
        lease_fields = {
            "field1": [
                ExtractedLeaseField(
                    type=ExtractedLeaseFieldType.STRING,
                    valueString="lease_value",
                    confidence=0.9,
                    date_of_document=date(2023, 1, 1),
                    document="test_LSE_doc.pdf"  # LSE document
                ),
                ExtractedLeaseField(
                    type=ExtractedLeaseFieldType.STRING,
                    valueString="amendment_value",
                    confidence=0.8,
                    date_of_document=date(2023, 6, 1),
                    document="test_AMD_doc.pdf"  # AMD document
                )
            ]
        }

        existing_document = ExtractedCollectionDocuments(
            collection_id="test_collection",
            config_id="config-id",
            lease_config_hash="test_hash",
            information=ExtractedCollectionInformationCollection(
                leases=[
                    ExtractedLeaseCollection(
                        lease_id="test_lease",
                        original_documents=["test_LSE_doc.pdf", "test_AMD_doc.pdf"],
                        markdowns=["test_LSE_doc.md", "test_AMD_doc.md"],
                        fields=lease_fields
                    )
                ]
            )
        )

        self.mock_collection_documents_collection.find_one.return_value = existing_document.model_dump()

        result = self.service._get_all_extracted_fields_from_collection_doc("test_collection", self.config)

        # Should have separate entries for lease and non-lease documents
        self.assertEqual(len(result), 1)
        self.assertIn("test_lease", result)

        lease_result = result["test_lease"]
        self.assertIn("field1", lease_result)

        # Should have 2 entries: 1 lease agreement data + 1 max field value
        self.assertEqual(len(lease_result["field1"]), 2)
        self.assertEqual(lease_result, {
            "field1": [
                LeaseAgreementDocumentData(
                    type=ExtractedLeaseFieldType.STRING,
                    valueString="lease_value",
                    confidence=0.9,
                    date_of_document=date(2023, 1, 1),
                    document="test_LSE_doc.pdf"
                ),
                LeaseAgreementDocumentData(
                    type=ExtractedLeaseFieldType.STRING,
                    valueString="amendment_value",
                    confidence=0.8,
                    date_of_document=date(2023, 6, 1),
                    document="test_AMD_doc.pdf"
                )
            ]
        })

    @patch("services.ingest_lease_documents_service.logging")
    def test_get_all_extracted_fields_duplicate_lease_ids(self, mock_logging):
        """Test handling of duplicate lease IDs (should skip duplicates)."""
        lease_fields = {
            "field1": [
                ExtractedLeaseField(
                    type=ExtractedLeaseFieldType.STRING,
                    valueString="test_value",
                    confidence=0.9,
                    date_of_document=date(2023, 1, 1),
                    document="test_doc.pdf"
                )
            ]
        }

        existing_document = ExtractedCollectionDocuments(
            collection_id="test_collection",
            config_id="config-id",
            lease_config_hash="test_hash",
            information=ExtractedCollectionInformationCollection(
                leases=[
                    ExtractedLeaseCollection(
                        lease_id="duplicate_lease",
                        original_documents=["doc1.pdf"],
                        markdowns=["doc1.md"],
                        fields=lease_fields
                    ),
                    ExtractedLeaseCollection(
                        lease_id="duplicate_lease",  # Same ID
                        original_documents=["doc2.pdf"],
                        markdowns=["doc2.md"],
                        fields=lease_fields
                    )
                ]
            )
        )

        self.mock_collection_documents_collection.find_one.return_value = existing_document.model_dump()

        result = self.service._get_all_extracted_fields_from_collection_doc("test_collection", self.config)

        # Should only process first lease with duplicate ID
        self.assertEqual(len(result), 1)
        self.assertIn("duplicate_lease", result)

        mock_logging.error.assert_called_with(
            "A lease with ID duplicate_lease has already been processed - skipping..."
        )

    @patch("services.ingest_lease_documents_service.logging")
    def test_get_all_extracted_fields_multiple_lease_agreements(self, mock_logging):
        """Test handling of multiple lease agreement documents for the same field."""
        lease_fields = {
            "field1": [
                ExtractedLeaseField(
                    type=ExtractedLeaseFieldType.STRING,
                    valueString="lease1_value",
                    confidence=0.9,
                    date_of_document=date(2023, 1, 1),
                    document="test1_LSE_doc.pdf"
                ),
                ExtractedLeaseField(
                    type=ExtractedLeaseFieldType.STRING,
                    valueString="lease2_value",
                    confidence=0.85,
                    date_of_document=date(2023, 2, 1),
                    document="test2_LSE_doc.pdf"
                )
            ]
        }

        existing_document = ExtractedCollectionDocuments(
            collection_id="test_collection",
            config_id="config-id",
            lease_config_hash="test_hash",
            information=ExtractedCollectionInformationCollection(
                leases=[
                    ExtractedLeaseCollection(
                        lease_id="test_lease",
                        original_documents=["test1_LSE_doc.pdf", "test2_LSE_doc.pdf"],
                        markdowns=["test1_LSE_doc.md", "test2_LSE_doc.md"],
                        fields=lease_fields
                    )
                ]
            )
        )

        self.mock_collection_documents_collection.find_one.return_value = existing_document.model_dump()

        result = self.service._get_all_extracted_fields_from_collection_doc("test_collection", self.config)

        # Should have entries for both lease agreements
        lease_result = result["test_lease"]
        self.assertIn("field1", lease_result)
        self.assertEqual(len(lease_result["field1"]), 2)  # 2 lease agreement data

    @patch("services.ingest_lease_documents_service.logging")
    def test_get_all_extracted_fields_empty_leases(self, mock_logging):
        """Test with a document that has no leases."""
        existing_document = ExtractedCollectionDocuments(
            collection_id="test_collection",
            config_id="config-id",
            lease_config_hash="test_hash",
            information=ExtractedCollectionInformationCollection(leases=[])
        )

        self.mock_collection_documents_collection.find_one.return_value = existing_document.model_dump()

        result = self.service._get_all_extracted_fields_from_collection_doc("test_collection", self.config)

        self.assertEqual(result, {})

    @patch("services.ingest_lease_documents_service.logging")
    def test_get_all_extracted_fields_collection_id_case_handling(self, mock_logging):
        """Test that collection_id is converted to uppercase when querying."""
        self.mock_collection_documents_collection.find_one.return_value = None

        self.service._get_all_extracted_fields_from_collection_doc("lowercase_collection", self.config)

        # Verify that the collection_id was converted to uppercase in the query
        self.mock_collection_documents_collection.find_one.assert_called_with(
            {"_id": "LOWERCASE_COLLECTION-test_hash"}
        )

    @patch("services.ingest_lease_documents_service.logging")
    def test_get_all_extracted_fields_document_exists_but_invalid_structure(self, mock_logging):
        """Test when document exists in database but has invalid structure that can't be parsed."""
        # Return a document that exists but has invalid structure
        invalid_document = {"_id": "test_collection-test_hash", "invalid_field": "invalid_data"}
        self.mock_collection_documents_collection.find_one.return_value = invalid_document

        # Mock ExtractedCollectionDocuments.model_validate to return None (simulating parsing failure)
        with patch("services.ingest_lease_documents_service.ExtractedCollectionDocuments.model_validate", return_value=None):
            result = self.service._get_all_extracted_fields_from_collection_doc("test_collection", self.config)

        self.assertEqual(result, {})
        mock_logging.warning.assert_called_with(
            "data for collection test_collection and lease config hash test_hash does not exist."
        )


if __name__ == '__main__':
    unittest.main()
