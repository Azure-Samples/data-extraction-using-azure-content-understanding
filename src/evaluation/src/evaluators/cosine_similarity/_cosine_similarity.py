from promptflow._utils.async_utils import async_run_allowing_running_loop

import numpy as np
from openai import AzureOpenAI


class _AsyncCosineSimilarityEvaluator:
    _openai_client: AzureOpenAI
    _model_name: str

    def __init__(self, model_config: dict):
        del model_config["type"]
        self._openai_client = AzureOpenAI(
            **model_config
        )
        self._model_name = model_config.get("azure_deployment", "text-embedding-ada-002")

    async def __call__(self, *, response: str, ground_truth: str, **kwargs):
        def get_embedding(text):
            response = self._openai_client.embeddings.create(input=text, model=self._model_name)
            embedding = response.data[0].embedding
            return embedding

        target_embedding = get_embedding(ground_truth)
        response_embedding = get_embedding(response)

        cosine_similarity = np.dot(target_embedding, response_embedding) / (
            np.linalg.norm(target_embedding) * np.linalg.norm(response_embedding)
        )
        return {"cosine_similarity": cosine_similarity}


class CosineSimilarityEvaluator:
    """Evaluator that computes the cosine similarity between two text embeddings.

    **Usage**

    .. code-block:: python

        eval_fn = CosineSimilarityEvaluator(model_config)
        result = eval_fn(
            response="Tokyo is the capital of Japan.",
            ground_truth="Tokyo is the capital city of Japan.")

    **Output format**

    .. code-block:: python

        {
            "cosine_similarity": 0.98
        }
    """
    def __init__(self, model_config):
        """Initializes the CosineSimilarityEvaluator."""
        self._async_evaluator = _AsyncCosineSimilarityEvaluator(model_config)

    def __call__(self, *, response: str, ground_truth: str, **kwargs):
        """Uses the async evaluator to compute the cosine similarity.

        Args:
            response (str): The response string.
            ground_truth (str): The ground_truth string.
            **kwargs: Additional keyword arguments.

        Returns:
            dict: A dictionary containing the cosine similarity.
        """
        return async_run_allowing_running_loop(
            self._async_evaluator, response=response, ground_truth=ground_truth, **kwargs
        )

    def _to_async(self):
        return self._async_evaluator
