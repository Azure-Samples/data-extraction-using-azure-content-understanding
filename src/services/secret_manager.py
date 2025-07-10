from azure.keyvault.secrets import SecretClient
from azure.core.credentials import TokenCredential
from azure.identity import DefaultAzureCredential
from typing import Optional
from utils import Singleton


class SecretManager(metaclass=Singleton):
    _secret_client: SecretClient

    def __init__(self, secret_client: SecretClient):
        """Initializes the SecretManager with a Key Vault URL and credentials.

        Args:
            secret_client (SecretClient): The SecretClient instance.
        """
        self._secret_client = secret_client

    def get_secret_value(self, secret_name: str) -> str:
        """Retrieves a secret value from the Key Vault.

        Args:
            secret_name (str): The name of the secret to retrieve.

        Returns:
            str: The value of the secret.
        """
        secret = self._secret_client.get_secret(secret_name)
        return secret.value

    def list_secrets(self) -> list:
        """Lists all secrets in the Key Vault.

        Returns:
            list: A list of secret names available in the Key Vault.
        """
        secrets = self._secret_client.list_properties_of_secrets()
        return [secret.name for secret in secrets]

    @classmethod
    def from_url(cls, keyvault_url: str, credential: Optional[TokenCredential] = None):
        """Creates a SecretManager instance from a Key Vault URL.

        Args:
            keyvault_url (str): The URL of the Azure Key Vault.

        Returns:
            SecretManager: An instance of SecretManager.
        """
        secret_client = SecretClient(
            vault_url=keyvault_url,
            credential=DefaultAzureCredential() if credential is None else credential,
        )
        return cls(secret_client)
