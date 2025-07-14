import json
from pathlib import Path
from unittest import TestCase
from datetime import date
from parameterized import parameterized

from src.models.extracted_collection_documents import (
    ExtractedCollectionDocuments,
    ExtractedLeaseField,
    ExtractedLeaseFieldType
)


class TestExtractedCollectionDocuments(TestCase):
    def test_extracted_site_collection_from_json(self):
        json_path = Path(__file__).parent / "lease_documents/sample-1.json"
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        site_collection = ExtractedCollectionDocuments.model_validate(data)

        self._validate_top_level_fields(site_collection, data)
        self._validate_information_leases(site_collection.information, data["information"])

    def _validate_top_level_fields(self, site_collection, data):
        self.assertEqual(site_collection.id, data["_id"])
        self.assertEqual(site_collection.is_locked, data["is_locked"])
        self.assertEqual(site_collection.unlock_unix_timestamp, data["unlock_unix_timestamp"])
        self.assertEqual(site_collection.site_id, data["site_id"])
        self.assertEqual(site_collection.config_id, data["config_id"])
        self.assertEqual(site_collection.lease_config_hash, data["lease_config_hash"])

    def _validate_information_leases(self, model_info, info):
        self.assertEqual(len(model_info.leases), len(info["leases"]))

        for lease_idx, lease in enumerate(info["leases"]):
            model_lease = model_info.leases[lease_idx]
            self._validate_lease(model_lease, lease)

    def _validate_lease(self, model_lease, lease):
        self.assertEqual(model_lease.lease_id, lease["lease_id"])
        self.assertEqual(model_lease.original_documents, lease["original_documents"])
        self.assertEqual(model_lease.markdowns, lease["markdowns"])
        self.assertEqual(set(model_lease.fields.keys()), set(lease["fields"].keys()))

        for field_key, field_list in lease["fields"].items():
            model_field_list = model_lease.fields[field_key]
            self.assertEqual(len(model_field_list), len(field_list))
            for field_idx, field in enumerate(field_list):
                self._validate_field(model_field_list[field_idx], field)

    def _validate_field(self, model_field, field):
        self.assertEqual(model_field.type.value, field["type"])
        self.assertEqual(model_field.date_of_document.isoformat(), field["date_of_document"])
        self.assertEqual(model_field.markdown, field["markdown"])
        self.assertEqual(model_field.document, field["document"])
        if "valueArray" in field and field["valueArray"] is not None:
            self._validate_value_array(model_field.valueArray, field["valueArray"])

    def _validate_value_array(self, model_value_array, value_array):
        self.assertIsNotNone(model_value_array)
        self.assertEqual(len(model_value_array), len(value_array))
        for arr_idx, arr_item in enumerate(value_array):
            self._validate_value_array_item(model_value_array[arr_idx], arr_item)

    def _validate_value_array_item(self, model_arr_item, arr_item):
        self.assertEqual(model_arr_item.type.value, arr_item["type"])
        if "valueObject" in arr_item and arr_item["valueObject"] is not None:
            self._validate_value_object(model_arr_item.valueObject, arr_item["valueObject"])

    def _validate_value_object(self, model_value_object, value_object):
        self.assertIsNotNone(model_value_object)
        self.assertEqual(set(model_value_object.keys()), set(value_object.keys()))
        for obj_key, obj_val in value_object.items():
            self._validate_value_object_item(model_value_object[obj_key], obj_val)

    def _validate_value_object_item(self, model_obj_val, obj_val):
        self.assertEqual(model_obj_val.type.value, obj_val["type"])
        if "valueString" in obj_val:
            self.assertEqual(model_obj_val.valueString, obj_val["valueString"])
        if "confidence" in obj_val:
            self.assertAlmostEqual(model_obj_val.confidence, obj_val["confidence"])
        if "spans" in obj_val:
            self.assertEqual(model_obj_val.spans, obj_val["spans"])
        if "source" in obj_val:
            self.assertEqual(model_obj_val.source, obj_val["source"])


class TestExtractedLeaseFieldIsLease(TestCase):
    """Test cases for the is_lease property of ExtractedLeaseField."""

    def setUp(self):
        """Set up test fixtures."""
        self.base_field_data = {
            "type": ExtractedLeaseFieldType.STRING,
            "valueString": "test_value",
            "spans": [],
            "confidence": 0.9,
            "source": "test_source",
            "date_of_document": date(2023, 1, 1),
            "markdown": "test.md"
        }

    def test_is_lease_with_lse_document(self):
        """Test that LSE documents are identified as lease documents."""
        field = ExtractedLeaseField(
            **self.base_field_data,
            document="Sites/market1/AR01407A/20130802/AR01407A_LSE_CELLSITE_20130802.pdf"
        )
        self.assertTrue(field.is_lease)

    def test_is_lease_with_sla_document(self):
        """Test that SLA documents are identified as lease documents."""
        field = ExtractedLeaseField(
            **self.base_field_data,
            document="Sites/market1/AR01407A/20130802/AR01407A_SLA_CELLSITE_20130802.pdf"
        )
        self.assertTrue(field.is_lease)

    @parameterized.expand([
        ("AR01407A_AMDA_CELLSITE_20130802.pdf"),
        ("AR01407A_AMD_CELLSITE_20130802.pdf"),
        ("AR01407A_AGREE_CELLSITE_20130802.pdf")
    ])
    def test_is_lease_with_other_document_types(self, document_name):
        """Test that other document types are NOT identified as lease documents."""
        field = ExtractedLeaseField(
            **self.base_field_data,
            document=f"Sites/market1/AR01407A/20130802/{document_name}"
        )
        self.assertFalse(field.is_lease)

    @parameterized.expand([
        ("AR01407A_lse_CELLSITE_20130802.pdf", True),
        ("AR01407A_LSE_CELLSITE_20130802.pdf", True),
        ("AR01407A_Lse_CELLSITE_20130802.pdf", True),
        ("AR01407A_sla_CELLSITE_20130802.pdf", True),
        ("AR01407A_SLA_CELLSITE_20130802.pdf", True),
        ("AR01407A_Sla_CELLSITE_20130802.pdf", True),
        ("AR01407A_amd_CELLSITE_20130802.pdf", False),
        ("AR01407A_AMD_CELLSITE_20130802.pdf", False),
        ("AR01407A_Amd_CELLSITE_20130802.pdf", False)
    ])
    def test_is_lease_case_insensitive(self, document_name, expected_result):
        """Test that document type checking is case insensitive."""
        field = ExtractedLeaseField(
            **self.base_field_data,
            document=f"Sites/market1/AR01407A/20130802/{document_name}"
        )
        self.assertEqual(field.is_lease, expected_result)

    def test_is_lease_with_no_document(self):
        """Test that fields with no document return False."""
        field = ExtractedLeaseField(
            **self.base_field_data,
            document=None
        )
        self.assertFalse(field.is_lease)

    def test_is_lease_with_empty_document(self):
        """Test that fields with empty document string return False."""
        field = ExtractedLeaseField(
            **self.base_field_data,
            document=""
        )
        self.assertFalse(field.is_lease)

    @parameterized.expand([
        ("AR01407A.pdf"),
        ("singlefilename.pdf"),
        ("AR01407A_.pdf")
    ])
    def test_is_lease_with_insufficient_parts(self, document_name):
        """Test that documents with insufficient filename parts return False."""
        field = ExtractedLeaseField(
            **self.base_field_data,
            document=f"Sites/market1/AR01407A/20130802/{document_name}"
        )
        self.assertFalse(field.is_lease)

    @parameterized.expand([
        ("AR01407A_LSE_CELLSITE_20130802.pdf"),
        ("/path/to/AR01407A_LSE_CELLSITE_20130802.pdf"),
        ("C:\\Windows\\path\\AR01407A_LSE_CELLSITE_20130802.pdf"),
        ("Sites/market1/site/lease/AR01407A_LSE_CELLSITE_20130802.pdf"),
        ("folder1/folder2/folder3/AR01407A_SLA_CELLSITE_20130802.pdf")
    ])
    def test_is_lease_with_different_path_structures(self, document_path):
        """Test that is_lease works correctly with different path structures."""
        field = ExtractedLeaseField(
            **self.base_field_data,
            document=document_path
        )
        self.assertTrue(field.is_lease)

    @parameterized.expand([
        ("SITE123_LSE_DOCUMENT_20231201.pdf", True),
        ("ABC123XYZ_SLA_CONTRACT_20231201.pdf", True),
        ("COMPLEX_SITE_NAME_LSE_VERY_LONG_DESCRIPTION_20231201.pdf", False),
        ("SHORT_SLA_20231201.pdf", True),
        ("SITE_AMD_20231201.pdf", False),
        ("SITE_DOC_20231201.pdf", False),
        ("SITE_OTHER_20231201.pdf", False)
    ])
    def test_is_lease_with_different_filename_patterns(self, document_name, expected_result):
        """Test various filename patterns that should be recognized as lease documents."""
        field = ExtractedLeaseField(
            **self.base_field_data,
            document=f"Sites/market1/site1/lease1/{document_name}"
        )
        self.assertEqual(field.is_lease, expected_result)
