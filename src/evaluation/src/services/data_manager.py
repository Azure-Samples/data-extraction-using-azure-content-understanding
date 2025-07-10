import os
import json
import pandas as pd
from azure.ai.ml import MLClient
from azure.ai.ml.constants import AssetTypes
from azure.ai.ml.entities import Data
import azure.ai.ml._artifacts._artifact_utilities as artifact_utilities
from ..constants import DATASET_ROOT_DIR, EXPERIMENT_ROOT_DIR
from models.data_collection_config import FieldDataCollectionConfig


class DataManager(object):
    _ml_client: MLClient

    def __init__(self, ml_client: MLClient):
        """Initializes the DataManager with the given MLClient."""
        self._ml_client = ml_client

    def _load_jsonl_files(self, path: str) -> pd.DataFrame:
        data = []
        for file in os.listdir(path):
            with open(os.path.join(path, file), "r") as f:
                for line in f:
                    data.append(json.loads(line))
        return pd.DataFrame(data)

    def upload_dataset(
        self,
        name: str,
        version: str,
        experiment_id: str,
        data: pd.DataFrame,
        config: FieldDataCollectionConfig
    ) -> str:
        """Uploads the dataset to the given name and version.

        Args:
            name (str): The name of the dataset.
            version (str): The version of the dataset.
            experiment_id (str): The ID of the experiment.
            data (pd.DataFrame): The dataset to upload.
            config (FieldDataCollectionConfig): The configuration object.
        """
        output_path = os.path.join(EXPERIMENT_ROOT_DIR, name, version, experiment_id)
        os.makedirs(output_path, exist_ok=True)
        output_file = os.path.join(output_path, "data.jsonl")
        data.to_json(output_file, orient="records", lines=True)

        data = Data(
            name=f"{name}-{version}-evaluation",
            version=experiment_id,
            path=output_file,
            type=AssetTypes.URI_FILE,
            tags={
                "source": "evaluation",
                "experiment_id": experiment_id,
                "config": config.model_dump_json(),
            },
        )

        return self._ml_client.data.create_or_update(data).id

    def get_dataset(self, name: str, version: str) -> pd.DataFrame:
        """Gets the dataset from the given name and version.

        Args:
            name (str): The name of the dataset.
            version (str): The version of the dataset.

        Returns:
            pd.DataFrame: The dataset as a pandas DataFrame.
        """
        output_path = os.path.join(DATASET_ROOT_DIR, name, version)
        if os.path.exists(output_path):
            return self._load_jsonl_files(output_path)

        os.makedirs(output_path, exist_ok=True)
        dataset = self._ml_client.data.get(name, version)
        artifact_utilities.download_artifact_from_aml_uri(
            dataset.path,
            output_path,
            self._ml_client.datastores
        )
        return self._load_jsonl_files(output_path)
