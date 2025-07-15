from unittest import TestCase
from utils.path_utils import (
    build_adls_markdown_file_path,
    build_adls_pdf_file_path
)
from models.ingestion_models import IngestDocumentType


class TestBuildAdlsMarkdownFilePath(TestCase):

    def test_when_md_file_return_md_file(self):
        """Tests the creation of a markdown file path given a markdown file."""
        # arrange
        doc_type = IngestDocumentType.COLLECTION
        file_name = "test_file.md"
        market = "test_market"
        collection_id = "test_collection_id"
        lease_id = "test_lease_id"

        expected_path = "Collections/test_market/test_collection_id/test_lease_id/test_file.md"

        # act
        result = build_adls_markdown_file_path(doc_type, collection_id, file_name, market, lease_id)

        # assert
        self.assertEqual(result, expected_path)

    def test_when_doc_type_is_lease_and_market_is_none(self):
        """Tests that a ValueError is raised when market is None for LEASE document type."""
        # arrange
        doc_type = IngestDocumentType.COLLECTION
        file_name = "test_file.md"
        market = None
        collection_id = "test_collection_id"
        lease_id = "test_lease_id"

        # act & assert
        with self.assertRaises(ValueError) as context:
            build_adls_markdown_file_path(doc_type, collection_id, file_name, market, lease_id)
        self.assertEqual(str(context.exception), "Market must be provided for COLLECTION document type.")

    def test_when_doc_type_is_lease_and_lease_id_is_none(self):
        """Tests that a ValueError is raised when lease_id is None for LEASE document type."""
        # arrange
        doc_type = IngestDocumentType.COLLECTION
        file_name = "test_file.md"
        market = "test_market"
        collection_id = "test_collection_id"
        lease_id = None

        # act & assert
        with self.assertRaises(ValueError) as context:
            build_adls_markdown_file_path(doc_type, collection_id, file_name, market, lease_id)
        self.assertEqual(str(context.exception), "Lease ID must be provided for COLLECTION document type.")


class TestBuildAdlsPdfFilePath(TestCase):

    def test_when_md_file_return_pdf_file(self):
        """Tests the creation of a PDF file path given a markdown file."""
        # arrange
        doc_type = IngestDocumentType.COLLECTION
        file_name = "test_file.md"
        market = "test_market"
        collection_id = "test_collection_id"
        lease_id = "test_lease_id"

        expected_path = "Collections/test_market/test_collection_id/test_lease_id/test_file.pdf"

        # act
        result = build_adls_pdf_file_path(doc_type, collection_id, file_name, market, lease_id)

        # assert
        self.assertEqual(result, expected_path)

    def test_when_market_is_none_raises_value_error(self):
        """Tests that a ValueError is raised when market is None for COLLECTION document type."""
        # arrange
        doc_type = IngestDocumentType.COLLECTION
        file_name = "test_file.pdf"
        market = None
        collection_id = "test_collection_id"
        lease_id = "test_lease_id"

        # act & assert
        with self.assertRaises(ValueError) as context:
            build_adls_pdf_file_path(doc_type, collection_id, file_name, market, lease_id)
        self.assertEqual(str(context.exception), "Market must be provided for COLLECTION document type.")

    def test_when_lease_id_is_none_raises_value_error(self):
        """Tests that a ValueError is raised when lease_id is None for COLLECTION document type."""
        # arrange
        doc_type = IngestDocumentType.COLLECTION
        file_name = "test_file.pdf"
        market = "test_market"
        collection_id = "test_collection_id"
        lease_id = None

        # act & assert
        with self.assertRaises(ValueError) as context:
            build_adls_pdf_file_path(doc_type, collection_id, file_name, market, lease_id)
        self.assertEqual(str(context.exception), "Lease ID must be provided for COLLECTION document type.")
