import unittest
from unittest.mock import MagicMock
from src.services.container_client import ContainerClient


class TestFileExists(unittest.TestCase):
    def setUp(self):
        """Set up the test case with a mock container client."""
        self.mock_container_client = MagicMock()
        self.container_client = ContainerClient(self.mock_container_client)

    def test_file_exists(self):
        """Test the file_exists method."""
        mock_blob_client = MagicMock()
        self.mock_container_client.get_blob_client.return_value = mock_blob_client
        mock_blob_client.exists.return_value = True

        result = self.container_client.file_exists("path/to/file.txt")

        self.mock_container_client.get_blob_client.assert_called_once_with("path/to/file.txt")
        mock_blob_client.exists.assert_called_once()
        self.assertTrue(result)


class TestUploadDocument(unittest.TestCase):
    def setUp(self):
        """Set up the test case with a mock container client."""
        self.mock_container_client = MagicMock()
        self.container_client = ContainerClient(self.mock_container_client)

    def test_upload_document(self):
        """Test the upload_document method."""
        self.container_client.upload_document(b"file content", "path/to/file.txt")

        self.mock_container_client.upload_blob.assert_called_once_with(
            "path/to/file.txt", b"file content", overwrite=True, metadata=None
        )


class TestDownloadFile(unittest.TestCase):
    def setUp(self):
        """Set up the test case with a mock container client."""
        self.mock_container_client = MagicMock()
        self.container_client = ContainerClient(self.mock_container_client)

    def test_download_file(self):
        """Test the download_file method."""
        mock_blob = MagicMock()
        self.mock_container_client.download_blob.return_value = mock_blob
        mock_blob.readall.return_value = b"file content"
        mock_blob.properties.metadata = {"key": "value"}

        b, metadata = self.container_client.download_file("path/to/file.txt")

        self.mock_container_client.download_blob.assert_called_once_with("path/to/file.txt")
        mock_blob.readall.assert_called_once()
        self.assertEqual(b, b"file content")
        self.assertEqual(metadata, {"key": "value"})
