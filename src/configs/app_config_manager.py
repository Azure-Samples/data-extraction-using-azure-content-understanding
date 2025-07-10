import os
import yaml
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from models.environment_config import EnvironmentConfig, ConfigurationValue, ConfigurationType
from services.secret_manager import SecretManager
from constants import ENVIRONMENT
from pydantic import BaseModel


class AppConfigManager:
    _env_config: EnvironmentConfig
    _secret_manager: SecretManager
    _has_hydrated: bool = False

    def __init__(
        self,
        env_config: EnvironmentConfig,
        secet_manager: SecretManager,
    ):
        """Initializes the AppConfigManager.

        Args:
            env_config (EnvironmentConfig): The environment configuration.
            secet_manager (SecretManager): The secret manager.
        """
        self._env_config = env_config
        self._secret_manager = secet_manager

    def hydrate_config(self):
        """Loads the configuration from the application.yaml file.

        Returns:
            dict: The configuration for the specified environment.
        """
        if self._has_hydrated:
            return self._env_config
        self._get_configuration_values(self._env_config)
        self._has_hydrated = True
        return self._env_config

    def _hydrate_value(self, config_value: ConfigurationValue) -> str:
        """Gets the value from an environment variable if the type is 'secret'.

        Args:
            config_value (ConfigurationValue): The configuration value.

        Returns:
            str: The resolved value.
        """
        if config_value.type != ConfigurationType.SECRET:
            return

        os_config_value = os.environ.get(config_value.key, None)
        if os_config_value:
            config_value.value = os_config_value
            return

        secret_value = self._secret_manager.get_secret_value(config_value.key)
        config_value.value = secret_value

    def _get_configuration_values(self, config: EnvironmentConfig):
        """Iterates over EnvironmentConfig to hydrate values.

        Args:
            config (EnvironmentConfig): The environment configuration.

        Returns:
            dict: A dictionary of configuration values.
        """
        def extract_values(prefix, obj):
            if isinstance(obj, ConfigurationValue):
                self._hydrate_value(obj)
            elif isinstance(obj, BaseModel):
                for key, value in obj.__dict__.items():
                    extract_values(f"{prefix}.{key}", value)

        extract_values("config", config)

    @classmethod
    def from_yaml(
        cls,
        config_path: str,
        environment: str,
        use_default_identity: bool = False,
    ):
        """Creates an instance of AppConfigManager from a YAML file.

        Args:
            config_path (str): Path to the YAML file.
            environment (str): The environment to load.
            use_default_identity (bool): Flag to use default identity.

        Returns:
            AppConfigManager: An instance of AppConfigManager.
        """
        config: dict
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"App Config YAML file not found: {config_path}"
            )
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing App Config YAML file: {e}")
        except Exception as e:
            raise Exception(f"An unexpected error occurred: {e}")

        config = config.get(environment, {})
        env_config = EnvironmentConfig.model_validate(config)

        credentials = None
        if env_config.user_managed_identity.client_id and not use_default_identity:
            credentials = ManagedIdentityCredential(
                client_id=env_config.user_managed_identity.client_id.value
            )
        else:
            credentials = DefaultAzureCredential()

        secret_manager = SecretManager.from_url(
            env_config.key_vault_uri,
            credentials
        )
        return cls(env_config, secret_manager)


_app_config_manager: AppConfigManager | None = None


def get_app_config_manager(use_default_identity: bool = False) -> AppConfigManager:
    """Returns the singleton instance of AppConfigManager.

    Args:
        use_default_identity (bool): Flag to use default identity.

    Returns:
        AppConfigManager: The singleton instance of AppConfigManager.
    """
    global _app_config_manager
    if not _app_config_manager:
        config_path = os.path.join(
            os.path.dirname(__file__), '../resources/app_config.yaml'
        )

        is_local = os.environ.get("ENVIRONMENT", "").lower() == "local"
        use_default_identity = use_default_identity or is_local

        _app_config_manager = AppConfigManager.from_yaml(
            config_path,
            ENVIRONMENT,
            use_default_identity
        )
    return _app_config_manager
