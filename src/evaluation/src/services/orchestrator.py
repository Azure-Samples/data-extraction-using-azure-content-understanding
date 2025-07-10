import logging
from time import time
from typing import Optional
from tqdm import tqdm
from .api_manager import ApiManager
from .data_manager import DataManager
from .evaluation_manager import EvaluationManager
from ..utils.bearer_token_utils import decode_bearer_token
from models.data_collection_config import FieldDataCollectionConfig


logger = logging.getLogger(__name__)


_ANSWER_KEY = "response"
_ERROR_KEY = "error"
_USER_ID_KEY = "preferred_username"
_EXPIRY_KEY = "exp"
_METRICS_KEY = "metrics"

_DEFAULT_TIME_OFFSET_IN_MINUTES = 15


class Orchestrator(object):
    _data_manager: DataManager
    _api_manager: ApiManager
    _evaluation_manager: EvaluationManager
    _config: FieldDataCollectionConfig

    def __init__(
        self,
        data_manager: DataManager,
        api_manager: ApiManager,
        evaluation_manager: EvaluationManager
    ):
        """Initializes the Orchestrator with the given DataManager and ApiManager."""
        self._data_manager = data_manager
        self._api_manager = api_manager
        self._evaluation_manager = evaluation_manager

    def _is_valid_token_expiry(
        self,
        bearer_token_data: dict,
        time_offset_in_minutes: int
    ) -> bool:
        if _EXPIRY_KEY not in bearer_token_data:
            return False

        expiry_time = bearer_token_data[_EXPIRY_KEY]
        current_time = time()
        time_offset = time_offset_in_minutes * 60

        return (expiry_time - current_time) > time_offset

    def run(
        self,
        dataset_name: str,
        dataset_version: str,
        config_name: Optional[str] = None,
        config_version: Optional[str] = None,
        use_default_config: bool = False,
        bearer_token: Optional[str] = None,
        user_id: Optional[str] = None,
        time_offset_in_minutes: int = _DEFAULT_TIME_OFFSET_IN_MINUTES
    ):
        """Runs the evaluation.

        Args:
            dataset_name (str): The name of the dataset.
            dataset_version (str): The version of the dataset.
            config_name (str): The name of the configuration.
            config_version (str): The version of the configuration.
            use_default_config (bool): Whether to use the default configuration.
            bearer_token (str): The bearer token for authentication.
            user_id (str): The user ID for the request.
            time_offset_in_minutes (int): The time offset in minutes to check for expiry.
        """
        experiment_id = str(int(time()))
        logger.info(f"Running evaluation for {dataset_name}:{dataset_version} -> {experiment_id}")

        user_id: str | None = user_id
        if bearer_token:
            token_data = decode_bearer_token(bearer_token)
            if not self._is_valid_token_expiry(token_data, time_offset_in_minutes):
                raise ValueError(
                    f"Bearer token is expired or is within the time offset of {time_offset_in_minutes} minutes. "
                    "Please update the token."
                )
            user_id = token_data.get(_USER_ID_KEY)

        logger.info("Getting config...")
        collection_config = self._api_manager.get_config(
            config_name,
            config_version,
            use_default_config,
            bearer_token,
            user_id,
        )

        logger.info("Loading data...")
        data = self._data_manager.get_dataset(dataset_name, dataset_version)

        if data.empty:
            raise ValueError("Dataset is empty - stopping evaluation.")

        logger.info("Running Inference...")
        for i, row in tqdm(data.iterrows(), total=len(data)):
            try:
                response = self._api_manager.chat(
                    row["Question"],
                    collection_config.name,
                    collection_config.version,
                    bearer_token=bearer_token,
                    user_id=user_id,
                )
                data.at[i, _ANSWER_KEY] = response.response or str()
                data.at[i, _METRICS_KEY] = response.metrics.model_dump_json() or str()
            except Exception as e:
                data.at[i, _ERROR_KEY] = str(e)

        data_id = self._data_manager.upload_dataset(
            name=dataset_name,
            version=dataset_version,
            experiment_id=experiment_id,
            data=data,
            config=collection_config,
        )

        logger.info("Evaluating...")
        self._evaluation_manager.evaluate(
            experiment_id,
            dataset_name,
            dataset_version,
            data_id,
            collection_config
        )
