from datetime import datetime
import time
from pymongo import errors
from pymongo.collection import Collection
from typing import Optional
from constants import MongoLockContants


class MongoLockManager:
    _collection: Collection
    _lock_duration: int

    def __init__(self, collection: Collection, lock_duration: int = MongoLockContants.LOCK_DURATION_IN_SECONDS):
        """Initialize the MongoLockManager.

        Args:
            collection (Collection): The MongoDB collection to use for locking.
            lock_duration (int): Duration of the lock in seconds.
        """
        self._collection = collection
        self._lock_duration = lock_duration

    def acquire_lock(self, document_id: str) -> bool:
        """Attempt to acquire a lock on a document.

        Args:
            document_id (str): The ID of the document to lock.
            lock_duration (int): Duration of the lock in seconds (default: 300 seconds).

        Returns:
            bool: True if the lock was acquired, False otherwise.
        """
        current_time = int(datetime.now().timestamp())
        unlock_time = current_time + self._lock_duration

        try:
            result = self._collection.update_one(
                {
                    "_id": document_id,
                    "$or": [
                        {"is_locked": {"$exists": False}},  # Field does not exist
                        {"is_locked": False},  # Document is not locked
                        {"unlock_unix_timestamp": {"$lte": current_time}}  # Lock has expired
                    ]
                },
                {
                    "$set": {
                        "is_locked": True,
                        "unlock_unix_timestamp": unlock_time
                    }
                },
                upsert=True
            )
            if result.modified_count > 0 or result.upserted_id is not None:
                return True
            return False
        except errors.PyMongoError as e:
            raise RuntimeError(f"Failed to acquire lock for document {document_id}: {e}")

    def wait(self, document_id: str, timeout: Optional[int] = MongoLockContants.MAX_WAIT_TIMEOUT_IN_SECONDS) -> bool:
        """Wait for a lock to be released on a document.

        Args:
            document_id (str): The ID of the document to wait for.
            timeout (int, optional): Maximum time to wait in seconds. If None, wait indefinitely.

        Returns:
            bool: True if the lock was released, False if timed out.
        """
        start_time = datetime.now()
        while True:
            if self.acquire_lock(document_id):
                return True
            if timeout and (datetime.now() - start_time).total_seconds() > timeout:
                return False
            time.sleep(MongoLockContants.WAIT_SLEEP_DURATION)

    def release_lock(self, document_id: str) -> bool:
        """Release the lock on a document.

        Args:
            document_id (str): The ID of the document to unlock.

        Returns:
            bool: True if the lock was released, False otherwise.
        """
        try:
            result = self._collection.update_one(
                {"_id": document_id, "is_locked": True},
                {
                    "$set": {
                        "is_locked": False,
                        "unlock_unix_timestamp": 0
                    }
                }
            )
            return result.modified_count > 0
        except errors.PyMongoError as e:
            raise RuntimeError(f"Failed to release lock for document {document_id}: {e}")
