import requests
from uuid import uuid4
from typing import Any, Dict, Optional
from models.api.v1 import QueryRequest, QueryResponse
from models.data_collection_config import FieldDataCollectionConfig


class ApiManager(object):
    _base_url: str
    _query_params: Dict[str, Any]

    def __init__(self, base_url: str, query_params: Dict[str, Any] = {}):
        """Initializes the ApiManager with the given base URL."""
        self._base_url = base_url
        self._query_params = query_params

    def _build_headers(
        self, bearer_token: Optional[str], user_id: Optional[str]
    ) -> dict:
        """Builds the headers for the request.

        Args:
            bearer_token (str): The bearer token for authentication.
            user_id (str): The user ID for the request.

        Returns:
            dict: The headers for the request.
        """
        headers = {}
        if bearer_token:
            headers["x-authorization"] = f"Bearer {bearer_token}"
        if user_id:
            headers["x-user"] = user_id
        return headers

    def chat(
        self,
        query: str,
        config_name: str,
        config_version: str,
        bearer_token: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> QueryResponse:
        """Sends a chat request to the API.

        Args:
            query (str): The query string.
            config_name (str): The name of the configuration.
            config_version (str): The version of the configuration.
            bearer_token (str, optional): The bearer token for authentication.
            user_id (str, optional): The user ID for the request.

        Returns:
            QueryResponse: The response from the API.
        """
        body = QueryRequest(
            uid=user_id,
            cid=str(uuid4()),
            sid=str(uuid4()),
            query=query,
        )

        headers = self._build_headers(bearer_token, user_id)
        response = requests.post(
            f"{self._base_url}/api/v1/query",
            json=body.model_dump(),
            params={
                **self._query_params,
                "config_name": config_name,
                "config_version": config_version,
            },
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return QueryResponse.model_validate(data)

    def get_config(
        self,
        config_name: Optional[str] = None,
        config_version: Optional[str] = None,
        use_default_config: bool = False,
        bearer_token: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> FieldDataCollectionConfig:
        """Gets the configuration from the API.

        Args:
            config_name (str, optional): The name of the configuration.
            config_version (str, optional): The version of the configuration.
            use_default_config (bool): Whether to use the default configuration.
            bearer_token (str, optional): The bearer token for authentication.
            user_id (str, optional): The user ID for the request.

        Returns:
            FieldDataCollectionConfig: The configuration object.
        """
        headers = self._build_headers(bearer_token, user_id)
        response: requests.Response
        if use_default_config:
            response = requests.get(
                f"{self._base_url}/api/configs/default",
                headers=headers,
                params={
                    **self._query_params,
                },
                timeout=10,
            )
        else:
            response = requests.get(
                f"{self._base_url}/api/configs/{config_name}/versions/{config_version}",
                headers=headers,
                params={
                    **self._query_params,
                },
                timeout=10,
            )
        response.raise_for_status()
        data = response.json()
        return FieldDataCollectionConfig.model_validate(data)
