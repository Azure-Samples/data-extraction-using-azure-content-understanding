from uuid import uuid4
from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Literal, Optional, Union


class DataType(str, Enum):
    """Datatype of the source."""
    LEASE_AGREEMENT = "LeaseAgreement"


class FieldMappingMethod(str, Enum):
    """The method used to extract the field."""
    EXTRACT = "extract"
    GENERATE = "generate"


class FieldMappingType(str, Enum):
    """The value type once the field is extracted."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    TIME = "time"
    OBJECT = "object"
    ARRAY = "array"

    def to_content_understanding_type(self):
        """Converts the field mapping type to a type understood by Azure Content Understanding.

        Returns:
            str: The corresponding type as a string.
        """
        mapping = {
            FieldMappingType.STRING: "string",      # Plain text
            FieldMappingType.INTEGER: "integer",    # 64-bit signed integer
            FieldMappingType.FLOAT: "number",       # Double precision floating point
            FieldMappingType.BOOLEAN: "boolean",    # Boolean value
            FieldMappingType.DATE: "date",          # ISO 8601 (YYYY-MM-DD) formatted date
            FieldMappingType.DATETIME: "date",      # ISO 8601 datetime
            FieldMappingType.TIME: "time",          # ISO 8601 (hh:mm:ss) formatted time
            FieldMappingType.OBJECT: "object",      # Named list of subfields
            FieldMappingType.ARRAY: "array",        # List of subfields of the same type
        }
        return mapping[self]


class FieldSchema(BaseModel):
    """Schema representation of the extracted field."""
    name: str
    type: FieldMappingType
    description: str
    method: FieldMappingMethod = FieldMappingMethod.EXTRACT


class ArrayFieldSchema(FieldSchema):
    type: Literal[FieldMappingType.ARRAY] = FieldMappingType.ARRAY
    items: List[FieldSchema]
    method: FieldMappingMethod = FieldMappingMethod.GENERATE


class BaseCollectionRow(BaseModel):
    """List of extracted fields, along with their schema, from the corresponding datatype of the source."""
    data_type: DataType
    field_schema: List[FieldSchema]


class ClassifierConfig(BaseModel):
    """Configuration for the CU classifier."""
    enabled: bool = False
    classifier_id: str = ""


class LeaseAgreementCollectionRow(BaseCollectionRow):
    """List of extracted fields, along with their schema, specific to Lease Agreement."""
    data_type: DataType = DataType.LEASE_AGREEMENT
    analyzer_id: str
    field_schema: List[Union[FieldSchema, ArrayFieldSchema]]
    classifier: Optional[ClassifierConfig] = None


class FieldDataCollectionConfig(BaseModel):
    """Data collection configuration that defines the list of extracted fields, along with the prompt used."""
    id: str = Field(..., alias="_id", default_factory=lambda: str(uuid4()))
    name: str
    version: str
    prompt: str
    lease_config_hash: str = ""
    collection_rows: list[LeaseAgreementCollectionRow]
