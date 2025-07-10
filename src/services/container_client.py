import os
import json
from typing import Union
from multiprocessing.pool import ThreadPool
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.storage.blob import ContainerClient as AzureContainerClient
from models.environment_config import EnvironmentConfig


_CONCURRENT_THREADS = 10


class ContainerClient(object):
    container_client: AzureContainerClient

    def __init__(self, container_client: AzureContainerClient):
        """Initialize the ContainerClient.

        Args:
            container_client (AzureContainerClient): The Azure ContainerClient instance.
        """
        self.container_client = container_client

    def _list_documents(self, base_path: str):
        files = self.container_client.list_blobs(base_path)
        return [file.name for file in files if os.path.splitext(file.name)[1]]

    def _download_and_save_file(self, path: str, output_dir: str):
        output_path, file_name = os.path.split(path)
        metadata_file_name = file_name.split(".")[0] + ".json"

        # remove all special characters from the path except for _ and -
        import re
        output_path = re.sub(r"[^a-zA-Z0-9_\-\/]", "", output_path)
        output_file = os.path.join(output_dir, output_path, file_name)
        metadata_output_file = os.path.join(
            output_dir,
            output_path,
            metadata_file_name
        )

        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        content, metadata = self.download_file(path)

        with open(output_file, "wb") as f:
            f.write(content)

        with open(metadata_output_file, "w") as f:
            json.dump(metadata, f, indent=4)

        return output_file

    def file_exists(self, file_path: str):
        """Check if a file exists in the blob storage.

        Args:
            file_path (str): The path of the file to check.

        Returns:
            bool: True if the file exists, False otherwise.
        """
        blob_client = self.container_client.get_blob_client(file_path)
        return blob_client.exists()

    def upload_document(self, bytes: Union[bytes, str], path: str, metadata: dict = None):
        """Upload a document to the blob storage.

        Args:
            bytes (Union[bytes, str]): The content of the document to upload.
            path (str): The path to upload the document to.
            metadata (dict, optional): Metadata to associate with the blob. Defaults to None.
        """
        self.container_client.upload_blob(path, bytes, overwrite=True, metadata=metadata)

    def download_file(self, path: str):
        """Download a file from the blob storage.

        Args:
            path (str): The path of the file to download.

        Returns:
            bytes: The content of the downloaded file.
        """
        blob = self.container_client.download_blob(path)
        content = blob.readall()
        metadata = blob.properties.metadata
        return content, metadata

    def download_files(self, base_path: str, output_dir: str, extension: str = None):
        """Download files from the blob storage.

        Args:
            base_path (str): The base path of the files to download.
            output_dir (str): The directory to save the downloaded files.
            extension (str, optional): The file extension to filter the files. Defaults to None.
        """
        files = self._list_documents(base_path)
        if extension:
            files = [file for file in files if file.endswith(extension)]
        parameters = [(file, output_dir) for file in files]
        with ThreadPool(processes=_CONCURRENT_THREADS) as pool:
            results = pool.starmap(self._download_and_save_file, parameters)
        return results


_container_client: ContainerClient | None = None


def get_container_client(environment_config: EnvironmentConfig) -> ContainerClient:
    """Get the ContainerClient instance.

    Args:
        environment_config (EnvironmentConfig): The environment configuration.

    Returns:
        ContainerClient: The ContainerClient instance.
    """
    global _container_client
    if _container_client is not None:
        return _container_client

    is_local = os.environ.get("ENVIRONMENT", "").lower() == "local"

    credential: str | DefaultAzureCredential
    if environment_config.user_managed_identity.client_id and not is_local:
        credential = ManagedIdentityCredential(
            client_id=environment_config.user_managed_identity.client_id.value
        )
    else:
        credential = DefaultAzureCredential()
    container_client = AzureContainerClient(
        account_url=environment_config.blob_storage.account_url.value,
        container_name=environment_config.blob_storage.container_name.value,
        credential=credential
    )
    _container_client = ContainerClient(container_client)
    return _container_client
