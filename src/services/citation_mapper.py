from typing import Tuple, Dict, Optional


_VALUE_PREFIX = 'value'
_VALUE_ARRAY_KEY = 'valueArray'
_VALUE_OBJECT_KEY = 'valueObject'
_SOURCE_KEY = 'source'
_DOCUMENT_KEY = 'document'
_TYPE_KEY = 'type'


class CitationMapper:
    def process_json(self, data: dict) -> Tuple[dict, Dict[str, str]]:
        """Process the JSON object to replace `source_document` and `source_bounding_boxes`.

        Replacing them with aliases and generate a mapping for the replacements.

        Args:
            data (dict): The input JSON object.

        Returns:
            Tuple[dict, Dict[str, str]]: The processed JSON object and the mapping.
        """
        mapping = {}
        id = data["_id"]
        alias_counter = 1

        # Process unstructured data
        for lease in data.get('leases_from_unstructured_data', []):
            self._replace_citations(lease.get('fields', {}), mapping, id, [alias_counter])
            alias_counter = alias_counter + len(lease.get('fields', {}))

        # Process structured data
        for lease in data.get('leases_from_structured_data', []):
            fields = lease.get('fields', {})
            for _, field_value in fields.items():
                if isinstance(field_value, dict):
                    if 'type' in field_value:
                        field_value.pop('type', None)
                if isinstance(field_value, list):
                    for item in field_value:
                        if 'type' in item:
                            item.pop('type', None)

        return data, mapping

    def _convert_number_to_excel_column(self, number):
        result = ""
        while number > 0:
            number -= 1
            result = chr(65 + (number % 26)) + result
            number //= 26
        return result

    def _process_dict_element(
        self,
        field_elem: dict,
        field_key: str,
        fields_to_delete: set,
        mapping: dict,
        id: str,
        alias_counter: list,
        document: Optional[str] = None
    ):
        """Helper method to process a dictionary element for citation replacement.

        Args:
            field_elem (dict): The dictionary element to process
            field_key (str): The key of the field being processed
            fields_to_delete (set): Set to track fields that should be deleted
            mapping (dict): The mapping dictionary to store the replacements
            id (str): The ID of the document
            alias_counter (list): A list containing a single integer to track the alias count
            document (Optional[str]): The document name to use for citation

        Returns:
            bool: True if the field should be kept, False if processing should continue to next field
        """
        field_keys = field_elem.keys()
        # check if a key starts with value
        if not any(key.startswith(_VALUE_PREFIX) for key in field_keys):
            fields_to_delete.add(field_key)
            return False

        if _TYPE_KEY in field_elem:
            field_elem.pop(_TYPE_KEY, None)

        if (_DOCUMENT_KEY in field_elem and field_elem[_DOCUMENT_KEY]) or document:
            _document = document or field_elem[_DOCUMENT_KEY]
            if _VALUE_ARRAY_KEY in field_elem:
                for item in field_elem[_VALUE_ARRAY_KEY]:
                    value_object = item[_VALUE_OBJECT_KEY]
                    self._replace_citations(value_object, mapping, id, alias_counter, _document)
                field_elem.pop(_DOCUMENT_KEY, None)
                return False

            alias = f"CITE{id}-{self._convert_number_to_excel_column(alias_counter[0])}"
            mapping[alias] = {
                "source_document": _document,
                "source_bounding_boxes": field_elem.get(_SOURCE_KEY)
            }
            field_elem[_DOCUMENT_KEY] = alias
            field_elem.pop(_SOURCE_KEY, None)
            alias_counter[0] += 1

        return True

    def _replace_citations(self, fields, mapping, id, alias_counter, document: Optional[str] = None):
        """Helper to replace citations in fields dict.

        Args:
            fields (dict): The fields dictionary containing the citations.
            mapping (dict): The mapping dictionary to store the replacements.
            id (str): The ID of the document.
            alias_counter (list): A list containing a single integer to track the alias count.
            document (Optional[str]): The document name to be used for the citation.
        """
        fields_to_delete = set()
        for field_key, field_value in fields.items():
            if isinstance(field_value, list):
                for field_elem in field_value:
                    if isinstance(field_elem, dict):
                        if not self._process_dict_element(
                                field_elem, field_key, fields_to_delete,
                                mapping, id, alias_counter, document):
                            continue
            elif isinstance(field_value, dict):
                if not self._process_dict_element(
                        field_value, field_key, fields_to_delete,
                        mapping, id, alias_counter, document):
                    continue

        # delete all fields that are not needed
        for field_key in fields_to_delete:
            fields.pop(field_key, None)
