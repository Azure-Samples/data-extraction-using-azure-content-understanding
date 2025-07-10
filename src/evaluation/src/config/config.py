import os
from pydantic import BaseModel
import yaml
from typing import Dict, Any
from dotenv import load_dotenv


load_dotenv()


_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "config.yaml"
)


class ApiConfig(BaseModel):
    """API configuration model."""
    base_url: str
    query_params: Dict[str, Any] = {}


class EnvironmentConfig(BaseModel):
    """Environment configuration model."""
    api: ApiConfig


environment_config: EnvironmentConfig | None = None


def load_config(environment: str) -> EnvironmentConfig:
    """Loads the configuration from the YAML file.

    Args:
        environment (str): The environment to load the configuration for.

    Returns:
        EnvironmentConfig: The loaded configuration object.
    """
    global environment_config
    if environment_config:
        return environment_config

    with open(_CONFIG_PATH, "r") as file:
        config = yaml.safe_load(file)
    if environment not in config:
        raise ValueError(f"Environment '{environment}' not found in configuration.")
    environment_config = EnvironmentConfig(**config.get(environment))
    return environment_config
