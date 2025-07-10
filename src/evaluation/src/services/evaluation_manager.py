# import time
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import Evaluation, Dataset, EvaluatorConfiguration
from azure.core.credentials import TokenCredential
from models.data_collection_config import FieldDataCollectionConfig
from azure.ai.evaluation import RougeType
import os
from ..constants import COSINE_SIMILARITY_ID, CORR_ID, TOKEN_LATENCY_ID


class EvaluationManager(object):
    _ai_project_client: AIProjectClient

    def __init__(self, ai_project_client: AIProjectClient):
        """Initializes the EvaluationManager with the given AIProjectClient.

        Args:
            ai_project_client (AIProjectClient): The AIProjectClient to use.
        """
        self._ai_project_client = ai_project_client

        self.default_connection = self._ai_project_client.connections.get(
            connection_name=os.getenv("CONNECTION_NAME", "qtmNpeGenAIWu2Oai1")
        )
        self.gpt_deployment_name = os.getenv("GPT_DEPLOYMENT_NAME", "gpt-4o")
        self.api_version = os.getenv("OPENAI_API_VERSION", "2023-05-15")

    def evaluate(
        self,
        experiment_id: str,
        dataset_name: str,
        dataset_version: str,
        data_id: str,
        config: FieldDataCollectionConfig
    ):
        """Evaluates the results and saves them to the given dataset.

        Args:
            experiment_id (str): The ID of the experiment.
            dataset_name (str): The name of the dataset.
            dataset_version (str): The version of the dataset.
            data_id (str): The ID of the data.
            config (FieldDataCollectionConfig): The configuration object.
        """
        data_mapping = {
            "query": "${data.Question}",
            "response": "${data.response}",
            "ground_truth": "${data.Answer}",
            "metrics": "${data.metrics}"
        }

        evaluation = Evaluation(
            display_name=f"{dataset_name}-{dataset_version}-{experiment_id}",
            tags={
                "config": config.model_dump_json(),
            },
            data=Dataset(id=data_id),
            evaluators={
                "similarity": EvaluatorConfiguration(
                    id="azureml://registries/azureml/models/Similarity-Evaluator/versions/3",
                    init_params={
                        "model_config": self.default_connection.to_evaluator_model_config(
                            deployment_name=self.gpt_deployment_name, api_version=self.api_version
                        )
                    },
                    data_mapping=data_mapping,
                ),
                "rouge": EvaluatorConfiguration(
                    id="azureml://registries/azureml/models/Rouge-Score-Evaluator/versions/3",
                    init_params={
                        "rouge_type": RougeType.ROUGE_L
                    },
                    data_mapping=data_mapping,
                ),
                "f1_score": EvaluatorConfiguration(
                    id="azureml://registries/azureml/models/F1Score-Evaluator/versions/3",
                    data_mapping=data_mapping,
                ),
                "Correctness": EvaluatorConfiguration(
                    id=f"azureml://locations/westus/workspaces/{CORR_ID}/versions/14",
                    init_params={
                        "model_config": self.default_connection.to_evaluator_model_config(
                            deployment_name=self.gpt_deployment_name, api_version=self.api_version
                        )
                    },
                    data_mapping=data_mapping,
                ),
                "coherence": EvaluatorConfiguration(
                    id="azureml://registries/azureml/models/Coherence-Evaluator/versions/5",
                    init_params={
                        "model_config": self.default_connection.to_evaluator_model_config(
                            deployment_name=self.gpt_deployment_name, api_version=self.api_version
                        )
                    },
                    data_mapping=data_mapping,
                ),
                "cosine_similarity": EvaluatorConfiguration(
                    id=f"azureml://locations/westus/workspaces/{COSINE_SIMILARITY_ID}/versions/4",
                    init_params={
                        "model_config": self.default_connection.to_evaluator_model_config(
                            deployment_name="text-embedding-ada-002", api_version="2024-10-21"
                        )
                    },
                    data_mapping=data_mapping,
                ),
                "cost": EvaluatorConfiguration(
                    id=f"azureml://locations/westus/workspaces/{TOKEN_LATENCY_ID}/versions/6",
                    data_mapping=data_mapping,
                )
            }
        )

        evaluation_response = self._ai_project_client.evaluations.create(
            evaluation=evaluation,
            params={"api-version": "2025-05-15-preview"}
        )

        print(f"Evaluation with ID {evaluation_response.id} and display name {evaluation_response.display_name}"
              " has been created; monitor its progress in the Azure AI Foundry UI.")

        # Commenting out for now as the params workaround to specify the api version
        # for the create() call isn't possible for the get() call in
        # azure-ai-projects versions 1.0.0b6-10.
        # Users will have to manually check the status of the evaluation
        # in the Foundry UI.
        # See https://github.com/Azure/azure-sdk-for-python/issues/41407#issuecomment-2941218871
        #
        # Note that version 1.0.0b11 might resolve this, but it also introduces breaking changes
        # as it requires the new Azure AI Foundry Project endpoint, and removes support for project
        # connection string and hub-based projects, so would likely require a new Foundry project resource.
        # See https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/ai/azure-ai-projects/CHANGELOG.md
        #
        # get_evaluation_response = self._ai_project_client.evaluations.get(
        #     evaluation_response.id,
        # )
        # status = get_evaluation_response.status
        # while status.lower() not in ["completed", "failed"]:
        #     get_evaluation_response = self._ai_project_client.evaluations.get(evaluation_response.id)
        #     status = get_evaluation_response.status
        #     time.sleep(5)
        #     print(f"Evaluation {evaluation_response.id} {status}")

    @classmethod
    def from_connection_string(cls, connection_string: str, credential: TokenCredential) -> "EvaluationManager":
        """Creates an EvaluationManager from the given connection string and credential.

        Args:
            connection_string (str): The connection string to use.
            credential (TokenCredential): The credential to use.

        Returns:
            EvaluationManager: The created EvaluationManager.
        """
        project_client = AIProjectClient.from_connection_string(
            connection_string,
            credential=credential,
        )
        return cls(project_client)
