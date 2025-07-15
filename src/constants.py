import os


ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")


class MongoLockContants(object):
    """Constants for MongoDB lock."""
    LOCK_DURATION_IN_SECONDS = 1
    WAIT_SLEEP_DURATION = 0.1
    MAX_WAIT_TIMEOUT_IN_SECONDS = 3


class PathConstants(object):
    """Constants for path."""
    COLLECTION_PREFIX = "Collections"
