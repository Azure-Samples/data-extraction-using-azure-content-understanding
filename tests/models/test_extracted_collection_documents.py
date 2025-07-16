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
    def test_extracted_collection_documents_from_json(self):
        json_path = Path(__file__).parent / "lease_documents/sample-1.json"
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        collection_documents = ExtractedCollectionDocuments.model_validate(data)

        self._validate_top_level_fields(collection_documents, data)
        self._validate_information_leases(collection_documents.information, data["information"])

    def _validate_top_level_fields(self, collection_documents, data):
        self.assertEqual(collection_documents.id, data["_id"])
        self.assertEqual(collection_documents.is_locked, data["is_locked"])
        self.assertEqual(collection_documents.unlock_unix_timestamp, data["unlock_unix_timestamp"])
        self.assertEqual(collection_documents.collection_id, data["collection_id"])
        self.assertEqual(collection_documents.config_id, data["config_id"])
        self.assertEqual(collection_documents.lease_config_hash, data["lease_config_hash"])

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
