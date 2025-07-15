import unittest
from unittest.mock import MagicMock
from pymongo.errors import PyMongoError
from src.services.mongo_lock_manager import MongoLockManager


class TestAcquireLock(unittest.TestCase):
    def setUp(self):
        """Set up the test case with a mock collection."""
        self.mock_collection = MagicMock()
        self.lock_manager = MongoLockManager(self.mock_collection, lock_duration=300)

    def test_acquire_lock_modified_count_success(self):
        """Test acquiring a lock when the document is modified."""
        self.mock_collection.update_one.return_value.modified_count = 1
        self.mock_collection.update_one.return_value.upserted_id = None

        result = self.lock_manager.acquire_lock("doc1")

        self.mock_collection.update_one.assert_called_once()
        self.assertTrue(result)

    def test_acquire_lock_upserted_id_success(self):
        """Test acquiring a lock when a new document is created."""
        self.mock_collection.update_one.return_value.modified_count = 0
        self.mock_collection.update_one.return_value.upserted_id = "new_doc_id"

        result = self.lock_manager.acquire_lock("doc1")

        self.mock_collection.update_one.assert_called_once()
        self.assertTrue(result)

    def test_acquire_lock_both_success(self):
        """Test acquiring a lock when both modified_count and upserted_id are successful."""
        self.mock_collection.update_one.return_value.modified_count = 1
        self.mock_collection.update_one.return_value.upserted_id = "new_doc_id"

        result = self.lock_manager.acquire_lock("doc1")

        self.mock_collection.update_one.assert_called_once()
        self.assertTrue(result)

    def test_acquire_lock_failure(self):
        """Test acquiring a lock when no document is found."""
        self.mock_collection.update_one.return_value.modified_count = 0
        self.mock_collection.update_one.return_value.upserted_id = None

        result = self.lock_manager.acquire_lock("doc1")

        self.mock_collection.update_one.assert_called_once()
        self.assertFalse(result)

    def test_acquire_lock_exception(self):
        """Test exception handling when acquiring a lock."""
        self.mock_collection.update_one.side_effect = PyMongoError("Mocked error")

        with self.assertRaises(RuntimeError):
            self.lock_manager.acquire_lock("doc1")


class TestWait(unittest.TestCase):
    def setUp(self):
        self.mock_collection = MagicMock()
        self.lock_manager = MongoLockManager(self.mock_collection, lock_duration=300)

    def test_wait_success(self):
        """Test waiting for a lock to be released."""
        self.lock_manager.acquire_lock = MagicMock(side_effect=[False, True])

        result = self.lock_manager.wait("doc1", timeout=5)

        self.assertTrue(result)
        self.lock_manager.acquire_lock.assert_called()

    def test_wait_timeout(self):
        """Test waiting for a lock to be released with timeout."""
        self.lock_manager.acquire_lock = MagicMock(return_value=False)

        result = self.lock_manager.wait("doc1", timeout=1)

        self.assertFalse(result)
        self.lock_manager.acquire_lock.assert_called()


class TestReleaseLock(unittest.TestCase):
    def setUp(self):
        """Set up the test case with a mock collection."""
        self.mock_collection = MagicMock()
        self.lock_manager = MongoLockManager(self.mock_collection, lock_duration=300)

    def test_release_lock_success(self):
        """Test releasing a lock successfully."""
        self.mock_collection.update_one.return_value.modified_count = 1

        result = self.lock_manager.release_lock("doc1")

        self.mock_collection.update_one.assert_called_once_with(
            {"_id": "doc1", "is_locked": True},
            {"$set": {"is_locked": False, "unlock_unix_timestamp": 0}}
        )
        self.assertTrue(result)

    def test_release_lock_failure(self):
        """Test releasing a lock when no document is found."""
        self.mock_collection.update_one.return_value.modified_count = 0

        result = self.lock_manager.release_lock("doc1")

        self.mock_collection.update_one.assert_called_once()
        self.assertFalse(result)

    def test_release_lock_exception(self):
        self.mock_collection.update_one.side_effect = PyMongoError("Mocked error")

        with self.assertRaises(RuntimeError):
            self.lock_manager.release_lock("doc1")
