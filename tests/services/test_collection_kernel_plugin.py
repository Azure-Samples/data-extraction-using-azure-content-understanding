from datetime import date
import json
import unittest
from unittest.mock import MagicMock
from models.data_collection_config import LeaseAgreementCollectionRow
from models.document_data_models import FieldMappingType, \
    LeaseAgreementDocumentData, \
    _LeaseAgreementDocumentData
from models.data_collection_config import FieldDataCollectionConfig, DataType
from services.collection_kernel_plugin import CollectionPlugin, document_data_cache
from models.document_data_models import DocumentData


class TestCollectionPlugin(unittest.TestCase):
    def setUp(self):
        # Create a sample FieldDataCollectionConfig
        self.config_cosmos_only = FieldDataCollectionConfig(
            id="test_id",
            name="test_name",
            version="1.0",
            lease_config_hash="fake_hash",
            prompt="test_prompt",
            collection_rows=[
                LeaseAgreementCollectionRow(
                    data_type="LeaseAgreement",
                    analyzer_id="analyzer",
                    field_schema=[
                        {
                            "name": "Name",
                            "type": "string",
                            "description": "Name"
                        },
                        {
                            "name": "Lease",
                            "type": "integer",
                            "description": "Lease number"
                        },
                        {
                            "name": "Current_Rent_Amount",
                            "type": "float",
                            "description": "Current rent amount"
                        }
                    ]
                )
            ]
        )

        self.config_cosmos_with_array = FieldDataCollectionConfig(
            id="test_id",
            name="test_name",
            version="1.0",
            lease_config_hash="fake_hash",
            prompt="test_prompt",
            collection_rows=[
                LeaseAgreementCollectionRow(
                    data_type="LeaseAgreement",
                    analyzer_id="analyzer",
                    field_schema=[
                        {
                            "name": "Name",
                            "type": "string",
                            "description": "Name"
                        },
                        {
                            "name": "Lease",
                            "type": "integer",
                            "description": "Lease number"
                        },
                        {
                            "name" : "equipment",
                            "type" : "array",
                            "description" : "equipment information",
                            "method" : "generate",
                            "items" : [
                                {
                                    "name" : "make",
                                    "type" : "string",
                                    "description" : "Make of the equipment",
                                    "method" : "extract"
                                },
                                {
                                    "name" : "quantity",
                                    "type" : "string",
                                    "description" : "Quantity of the equipment",
                                    "method" : "extract"
                                }
                            ]
                        },
                    ]
                )
            ]
        )

    def test_get_collection_data_cosmos_success(self):

        # Mock the IngestionCollectionDocumentService
        mock_lease_docs_service = MagicMock()

        plugin_cosmos_only = CollectionPlugin(
            config=self.config_cosmos_only,
            document_service=mock_lease_docs_service)

        collection_id = "3OAS074ACOS"

        mock_extracted_fields_cosmos_only = {
            "68313": {
                "Name": [LeaseAgreementDocumentData(
                    valueString="1 -  Rooftop",
                    source_document="/path/to/document_LSE_date.pdf",
                    source_bounding_boxes="D(1,1,1,1,1,1,1,1)",
                    date_of_document=date(2023, 10, 1)),
                    LeaseAgreementDocumentData(
                    valueString="2 -  Rooftop",
                    source_document="/path/to/document_AMD_date.pdf",
                    source_bounding_boxes="D(1,1,1,1,1,1,1,1)",
                    date_of_document=date(2023, 10, 1))],
                "Lease": [LeaseAgreementDocumentData(
                    valueInteger=68313,
                    source_document="/path/to/document_LSE_date.pdf",
                    source_bounding_boxes="D(1,1,1,1,1,1,1,1)",
                    date_of_document=date(2023, 10, 1)),
                    LeaseAgreementDocumentData(
                    valueInteger=68314,
                    source_document="/path/to/document_LSE_date.pdf",
                    source_bounding_boxes="D(1,1,1,1,1,1,1,1)",
                    date_of_document=date(2023, 10, 2))],
                "Current_Rent_Amount": [LeaseAgreementDocumentData(
                    valueNumber=18658.829,
                    source_document="/path/to/document_AMD_date.pdf",
                    source_bounding_boxes="D(1,1,1,1,1,1,1,1)",
                    date_of_document=date(2023, 10, 2))],
            }
        }

        mock_lease_docs_service._get_all_extracted_fields_from_collection_doc.return_value = mock_extracted_fields_cosmos_only

        # Execute the method
        response = plugin_cosmos_only.get_collection_data(collection_id)

        expected_response = {
            "_id": "3OAS074ACOS",
            "lease_config_hash": "fake_hash",
            "unstructured_data": [{
                "lease_id": "68313",
                "fields": {
                    "Name": [
                        {
                            "valueString": "1 -  Rooftop",
                            "date_of_document": "2023-10-01",
                            "document": "CITE3OAS074ACOS-A"
                        },
                        {
                            "valueString": "2 -  Rooftop",
                            "date_of_document": "2023-10-01",
                            "document": "CITE3OAS074ACOS-B"
                        }
                    ],
                    "Lease": [
                        {
                            "valueInteger": 68313,
                            "date_of_document": "2023-10-01",
                            "document": "CITE3OAS074ACOS-C"
                        },
                        {
                            "valueInteger": 68314,
                            "date_of_document": "2023-10-02",
                            "document": "CITE3OAS074ACOS-D"
                        }
                    ],
                    "Current_Rent_Amount": [{
                        "valueNumber": 18658.829,
                        "date_of_document": "2023-10-02",
                        "document": "CITE3OAS074ACOS-E"
                    }]
                }
            }]
        }

        self.assertEqual(json.loads(response), expected_response)

    def test_get_collection_data_cosmos_array_success(self):
        # Mock the IngestionCollectionDocumentService
        mock_lease_docs_service = MagicMock()

        plugin_cosmos_array = CollectionPlugin(
            config=self.config_cosmos_with_array,
            document_service=mock_lease_docs_service)

        collection_id = "3OAS074AARR"

        mock_extracted_fields_array = {
            "68313": {
                "Name": [LeaseAgreementDocumentData(
                    valueString="1 -  Rooftop",
                    source_document="/path/to/document1.pdf",
                    source_bounding_boxes="D(1,1,1,1,1,1,1,1)")],
                "Lease": [LeaseAgreementDocumentData(
                    valueInteger=68313,
                    source_document="/path/to/document2.pdf",
                    source_bounding_boxes="D(1,1,1,1,1,1,1,2)")],
                "equipment": [LeaseAgreementDocumentData(
                    valueArray=[
                        _LeaseAgreementDocumentData(
                            valueObject={
                                "make": _LeaseAgreementDocumentData(
                                    valueString="Make1",
                                    source_bounding_boxes="D(1,1,1,1,1,1,1,3)"),
                                "quantity": _LeaseAgreementDocumentData(
                                    valueString="10",
                                    source_bounding_boxes="D(1,1,1,1,1,1,1,4)")
                            }
                        )
                    ],
                    source_document="/path/to/document3.pdf",
                )]
            }
        }

        mock_lease_docs_service._get_all_extracted_fields_from_collection_doc.return_value = mock_extracted_fields_array

        # Execute the method
        response = plugin_cosmos_array.get_collection_data(collection_id)

        expected_response = {
            "_id": "3OAS074AARR",
            "lease_config_hash": "fake_hash",
            "unstructured_data": [{
                "lease_id": "68313",
                "fields": {
                    "Name": [{
                        "valueString": "1 -  Rooftop",
                        "document": "CITE3OAS074AARR-A"
                    }],
                    "Lease": [{
                        "valueInteger": 68313,
                        "document": "CITE3OAS074AARR-B"
                    }],
                    "equipment": [{
                        "valueArray": [
                            {
                                "valueObject": {
                                    "make": {
                                        "valueString": "Make1",
                                        "document": "CITE3OAS074AARR-C"
                                    },
                                    "quantity": {
                                        "valueString": "10",
                                        "document": "CITE3OAS074AARR-D"
                                    }
                                }
                            }
                        ]
                    }]
                }
            }]
        }

        self.assertEqual(response, json.dumps(expected_response))

    def test_get_collection_data_cosmos_array_missing_values_success(self):
        # Mock the IngestionCollectionDocumentService
        mock_lease_docs_service = MagicMock()

        plugin_cosmos_array = CollectionPlugin(
            config=self.config_cosmos_with_array,
            document_service=mock_lease_docs_service)

        collection_id = "4OAS074AARR"

        mock_extracted_fields_array = {
            "68313": {
                "Name": [LeaseAgreementDocumentData(
                    valueString="1 -  Rooftop",
                    source_document="/path/to/document1.pdf",
                    source_bounding_boxes="D(1,1,1,1,1,1,1,1)")],
                "Lease": [LeaseAgreementDocumentData(
                    valueInteger=68313,
                    source_document="/path/to/document2.pdf",
                    source_bounding_boxes="D(1,1,1,1,1,1,1,2)")],
                "equipment": [LeaseAgreementDocumentData(
                    valueArray=[
                        _LeaseAgreementDocumentData(
                            valueObject={
                                "make": _LeaseAgreementDocumentData(
                                    valueString="Make1",
                                    source_bounding_boxes="D(1,1,1,1,1,1,1,3)"),
                                "quantity": _LeaseAgreementDocumentData(
                                    valueString="10",
                                    source_bounding_boxes="D(1,1,1,1,1,1,1,4)")
                            }
                        ),
                        _LeaseAgreementDocumentData(
                            valueObject={
                                "make": _LeaseAgreementDocumentData(),
                                "quantity": _LeaseAgreementDocumentData(
                                    valueString="11",
                                    source_bounding_boxes="D(1,1,1,1,1,1,1,4)")
                            }
                        ),
                        _LeaseAgreementDocumentData(
                            valueObject={
                                "make": _LeaseAgreementDocumentData(
                                    valueString="Make2",
                                    source_bounding_boxes="D(1,1,1,1,1,1,1,3)"),
                                "quantity": _LeaseAgreementDocumentData()
                            }
                        ),
                        _LeaseAgreementDocumentData(
                            valueObject={
                                "make": _LeaseAgreementDocumentData(),
                                "quantity": _LeaseAgreementDocumentData()
                            }
                        )
                    ],
                    source_document="/path/to/document3.pdf",
                )]
            }
        }

        mock_lease_docs_service._get_all_extracted_fields_from_collection_doc.return_value = mock_extracted_fields_array

        # Execute the method
        response = plugin_cosmos_array.get_collection_data(collection_id)

        expected_response = {
            "_id": "4OAS074AARR",
            "lease_config_hash": "fake_hash",
            "unstructured_data": [{
                "lease_id": "68313",
                "fields": {
                    "Name": [{
                        "valueString": "1 -  Rooftop",
                        "document": "CITE4OAS074AARR-A"
                    }],
                    "Lease": [{
                        "valueInteger": 68313,
                        "document": "CITE4OAS074AARR-B"
                    }],
                    "equipment": [{
                        "valueArray": [
                            {
                                "valueObject": {
                                    "make": {
                                        "valueString": "Make1",
                                        "document": "CITE4OAS074AARR-C"
                                    },
                                    "quantity": {
                                        "valueString": "10",
                                        "document": "CITE4OAS074AARR-D"
                                    }
                                }
                            },
                            {
                                "valueObject": {
                                    "quantity": {
                                        "valueString": "11",
                                        "document": "CITE4OAS074AARR-E"
                                    }
                                }
                            },
                            {
                                "valueObject": {
                                    "make": {
                                        "valueString": "Make2",
                                        "document": "CITE4OAS074AARR-F"
                                    },
                                },
                            },
                            {
                                "valueObject": {}
                            }
                        ]
                    }]
                }
            }]
        }

        self.assertEqual(response, json.dumps(expected_response))

    def test_get_collection_data_cosmos_success_lease_without_lease_id(self):
        # Mock the IngestionCollectionDocumentService
        mock_lease_docs_service = MagicMock()

        plugin_cosmos_only = CollectionPlugin(
            config=self.config_cosmos_only,
            document_service=mock_lease_docs_service)

        collection_id = "3OAS074ANOID"

        mock_extracted_fields = {
            None: {
                "Name": [LeaseAgreementDocumentData(
                    valueString="1 -  Rooftop",
                    document="/path/to/document.pdf",
                    source="D(1,1,1,1,1,1,1,1)")],
                "Lease": [LeaseAgreementDocumentData(
                    valueInteger=68313,
                    document="/path/to/document.pdf",
                    source="D(1,1,1,1,1,1,1,1)")],
                "Current_Rent_Amount": [LeaseAgreementDocumentData(
                    valueNumber=18658.828,
                    document="/path/to/document.pdf",
                    source="D(1,1,1,1,1,1,1,1)")]
            }
        }

        mock_lease_docs_service._get_all_extracted_fields_from_collection_doc.return_value = mock_extracted_fields

        # Execute the method
        response = plugin_cosmos_only.get_collection_data(collection_id)

        # Verify the results
        expected_response = {
            "_id": "3OAS074ANOID",
            "lease_config_hash": "fake_hash",
            "unstructured_data": [{
                "fields": {
                    "Name": [{
                        "valueString": "1 -  Rooftop",
                        "document": "CITE3OAS074ANOID-A"
                    }],
                    "Lease": [{
                        "valueInteger": 68313,
                        "document": "CITE3OAS074ANOID-B"
                    }],
                    "Current_Rent_Amount": [{
                        "valueNumber": 18658.828,
                        "document": "CITE3OAS074ANOID-C"
                    }]
                }
            }]
        }

        self.assertEqual(response, json.dumps(expected_response))

    def test_get_collection_data_cosmos_empty_results(self):
        # Mock the IngestionCollectionDocumentService
        mock_lease_docs_service = MagicMock()

        plugin_cosmos_only = CollectionPlugin(
            config=self.config_cosmos_only,
            document_service=mock_lease_docs_service)

        collection_id = "3OAS074ACOSEMP"

        mock_extracted_fields = {}

        mock_lease_docs_service._get_all_extracted_fields_from_collection_doc.return_value = mock_extracted_fields

        # Execute the method
        response = plugin_cosmos_only.get_collection_data(collection_id)

        # Verify the results
        expected_document_data = DocumentData(_id=collection_id,
                                              lease_config_hash="fake_hash",
                                              unstructured_data=[])
        expected_response = json.dumps(expected_document_data.model_dump(by_alias=True), default=str)

        self.assertEqual(response, expected_response)


    def test_get_collection_lease_docs_service_exception(self):
        # Mock the IngestionCollectionDocumentService
        mock_lease_docs_service = MagicMock()

        # Create an instance of CollectionPlugin
        plugin_cosmos_only = CollectionPlugin(
            config=self.config_cosmos_only,
            document_service=mock_lease_docs_service)
        collection_id = "3OAS074AEXC"

        mock_lease_docs_service._get_all_extracted_fields_from_collection_doc.side_effect = \
            Exception("Lease docs service error")

        # Verify that an exception is raised
        with self.assertRaises(Exception) as context:
            plugin_cosmos_only.get_collection_data(collection_id)

        self.assertTrue("Lease docs service error" in str(context.exception))
