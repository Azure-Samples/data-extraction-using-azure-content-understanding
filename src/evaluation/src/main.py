import os
import click
import logging
import logging.config
import yaml
from azure.ai.ml.entities import Model
from azure.ai.ml import MLClient
from azure.core.credentials import TokenCredential
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from .services.data_manager import DataManager
from .services.api_manager import ApiManager
from .services.orchestrator import Orchestrator
from .services.evaluation_manager import EvaluationManager
from .config.config import load_config

load_dotenv()


_LOGGER_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "logger_config.yaml"
)


with open(_LOGGER_CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f.read())
    logging.config.dictConfig(config)


logger = logging.getLogger(__name__)


def _create_ml_client(connection_string: str, credential: TokenCredential) -> MLClient:
    """Creates a MLClient from the given connection string and credential.

    Args:
        connection_string (str): The connection string to use.
        credential (TokenCredential): The credential to use.

    Returns:
        MLClient: The MLClient.
    """
    _, subscription, resource_group, workspace = connection_string.split(";")
    ml_client = MLClient(
        credential=credential,
        subscription_id=subscription,
        resource_group_name=resource_group,
        workspace_name=workspace,
    )
    return ml_client


@click.group()
def cli():
    """CLI for the evaluation package."""
    pass


@cli.command()
@click.option(
    "--environment",
    type=click.Choice(["local", "dev", "uat"]),
    default="local",
    help="The environment to run the app in.",
)
@click.option(
    "--dataset-name",
    type=str,
    help="The name of the dataset to run the app on.",
    required=True,
)
@click.option(
    "--dataset-version",
    type=str,
    help="The version of the dataset to run the app on.",
)
@click.option(
    "--config-name",
    type=str,
    default="",
    help="The name of the config.",
)
@click.option(
    "--config-version",
    type=str,
    default="",
    help="The version of the config.",
)
@click.option(
    "--bearer-token",
    type=str,
    default="",
    help="The bearer token to use for authentication.",
)
@click.option(
    "--user-id",
    type=str,
    default="",
    help="The user ID to use for authentication.",
)
def eval(
    environment: str,
    dataset_name: str,
    dataset_version: str,
    config_name: str,
    config_version: str,
    bearer_token: str,
    user_id: str,
):
    """Run the evaluation.

    Args:
        environment (str): The environment to run the app in.
        dataset_name (str): The name of the dataset to run the app on.
        dataset_version (str): The version of the dataset to run the app on.
        config_name (str): The name of the config.
        config_version (str): The version of the config.
        bearer_token (str): The bearer token to use for authentication.
        user_id (str): The user ID to use for authentication.
    """
    logger.info("Starting evaluation...")

    use_default_config = False
    if (config_version.lower() == "none" and config_name.lower() == "none") or \
       (config_version == "" and config_name == ""):
        use_default_config = True
        logger.info("No config name or version provided. Using default config.")
    elif (config_version != "" and config_name != "") or \
         (config_version.lower() != "none" and config_name.lower() != "none"):
        logger.info(f"Using config {config_name}:{config_version}")
    else:
        raise ValueError("Config name and version must be provided together or not at all.")

    if bearer_token == "" or bearer_token.lower() == "none":
        bearer_token = None
        logger.info("No bearer token provided. Using None.")

    if user_id == "" or user_id.lower() == "none":
        user_id = None
        logger.info("No user ID provided. Using None.")

    if not user_id and not bearer_token:
        raise ValueError("Either bearer token or user ID must be provided.")

    credential = DefaultAzureCredential()

    azure_foundry_connection_string = os.environ.get("AZURE_FOUNDRY_CONNECTION_STRING")
    if not azure_foundry_connection_string:
        raise ValueError("AZURE_FOUNDRY_CONNECTION_STRING environment variable is not set.")

    config = load_config(environment)
    ml_client = _create_ml_client(azure_foundry_connection_string, credential)
    data_manager = DataManager(ml_client)
    api_manager = ApiManager(config.api.base_url, config.api.query_params)
    evaluation_manager = EvaluationManager.from_connection_string(
        azure_foundry_connection_string,
        credential
    )
    orchestrator = Orchestrator(
        data_manager,
        api_manager,
        evaluation_manager,
    )
    orchestrator.run(
        dataset_name,
        dataset_version,
        config_name,
        config_version,
        use_default_config,
        bearer_token,
        user_id
    )


@cli.command()
@click.option(
    "--evaluator-name",
    type=str,
    help="The name of the evaluator to upload.",
)
@click.option(
    "--evaluator-description",
    type=str,
    help="The description of the evaluator to upload.",
)
@click.option(
    "--evaluator-folder-name",
    type=str,
    help="The folder name of the evaluator to upload.",
)
def upload_evaluator(
    evaluator_name: str,
    evaluator_description: str,
    evaluator_folder_name: str,
):
    """Upload the evaluator to the registry.

    Args:
        evaluator_name (str): The name of the evaluator to upload.
        evaluator_description (str): The description of the evaluator to upload.
        evaluator_folder_name (str): The folder name of the evaluator to upload.
    """
    logger.info("Uploading evaluator...")

    credential = DefaultAzureCredential()

    azure_foundry_connection_string = os.environ.get("AZURE_FOUNDRY_CONNECTION_STRING")
    if not azure_foundry_connection_string:
        raise ValueError("AZURE_FOUNDRY_CONNECTION_STRING environment variable is not set.")

    ml_client = _create_ml_client(azure_foundry_connection_string, credential)
    model = Model(
        name=evaluator_name,
        description=evaluator_description,
        tags={"type": "evaluator"},
        path=os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "evaluators",
            evaluator_folder_name,
        )
    )

    ml_client.evaluators.create_or_update(
        model
    )


@cli.command()
@click.option(
    "--evaluator-name",
    type=str,
    help="The name of the evaluator to archive.",
)
@click.option(
    "--evaluator-version",
    type=str,
    help="The latest version of the evaluator to archive.",
)
def archive_evaluator(
    evaluator_name: str,
    evaluator_version: str
):
    """Archives an unused evaluator.

    Args:
        evaluator_name (str): The name of the evaluator to archive.
        evaluator_version (str): The latest version of the evaluator to archive.
    """
    logger.info("Archiving evaluator...")

    credential = DefaultAzureCredential()

    azure_foundry_connection_string = os.environ.get("AZURE_FOUNDRY_CONNECTION_STRING")
    if not azure_foundry_connection_string:
        raise ValueError("AZURE_FOUNDRY_CONNECTION_STRING environment variable is not set.")

    ml_client = _create_ml_client(azure_foundry_connection_string, credential)

    ml_client.models.archive(name=evaluator_name, version=evaluator_version)


@cli.command()
@click.option(
    "--evaluator-name",
    type=str,
    help="The name of the archived evaluator to restore.",
)
@click.option(
    "--evaluator-version",
    type=str,
    help="The latest version of the archived evaluator to restore.",
)
def restore_archived_evaluator(
    evaluator_name: str,
    evaluator_version: str
):
    """Restores an archived evaluator.

    Args:
        evaluator_name (str): The name of the archived evaluator to restore.
        evaluator_version (str): The latest version of the archived evaluator to restore.
    """
    logger.info("Restoring archived evaluator...")

    credential = DefaultAzureCredential()

    azure_foundry_connection_string = os.environ.get("AZURE_FOUNDRY_CONNECTION_STRING")
    if not azure_foundry_connection_string:
        raise ValueError("AZURE_FOUNDRY_CONNECTION_STRING environment variable is not set.")

    ml_client = _create_ml_client(azure_foundry_connection_string, credential)

    ml_client.models.restore(name=evaluator_name, version=evaluator_version)


if __name__ == "__main__":
    cli()
