from pydantic import BaseModel


class BaseMongoLockable(BaseModel):
    """Base class for MongoDB models with a lockable feature."""
    is_locked: bool = False
    unlock_unix_timestamp: int = 0
