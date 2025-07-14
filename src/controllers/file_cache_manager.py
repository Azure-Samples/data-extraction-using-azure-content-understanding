import os
import json


class FileCacheManager:
    """Handles file-based caching for analyzer outputs."""

    def __init__(self, cache_dir: str, is_local: bool):
        """Initializes the FileCacheManager.

        Args:
            cache_dir (str): The directory path where cache files will be stored.
            is_local (bool): Indicates whether the application is running in a local environment.
        """
        self.cache_dir = cache_dir
        self.is_local = is_local
        if self.is_local and not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def get_cache_key(self, collection_id, file_name, lease_hash):
        """Generates a cache key based on collection ID and lease hash.

        Args:
            collection_id (str): The collection identifier.
            file_name (str): The file name.
            lease_hash (str): The lease hash.

        Returns:
            str: The generated cache key.
        """
        # Normalize file name to make sure it can be a valid file name
        sanitized_file_name = file_name.replace('/', '_').replace('\\', '_')
        return f"{collection_id}-{sanitized_file_name}-{lease_hash}.json"

    def read(self, cache_key):
        """Reads cached data from a file if running in local mode.

        Args:
            cache_key (str): The cache key (filename).

        Returns:
            dict or None: The cached data if available, otherwise None.
        """
        if not self.is_local:
            return None
        cache_path = os.path.join(self.cache_dir, cache_key)
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def write(self, cache_key, data):
        """Writes data to a cache file if running in local mode.

        Args:
            cache_key (str): The cache key (filename).
            data (dict): The data to cache.
        """
        if not self.is_local:
            return
        cache_path = os.path.join(self.cache_dir, cache_key)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
