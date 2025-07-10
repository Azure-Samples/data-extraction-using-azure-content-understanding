from correctness_evaluator import CorrectnessEvaluator


class QACorrectnessEvaluator():
    _sdk_eval: CorrectnessEvaluator

    def __init__(self, model_config: dict):
        """Initialize QACorrectnessEvaluator with the given model configuration.

        Args:
            model_config (dict): Configuration for the model to be evaluated.
        """
        self._sdk_eval = CorrectnessEvaluator(model_config)

    def __call__(
        self,
        *,
        query: str,
        response: str,
        ground_truth: str,
    ) -> dict:
        """Evaluate the correctness of a response given a query and ground truth.

        Args:
            query (str): The input query.
            response (str): The model's response to the query.
            ground_truth (str): The expected correct response.

        Returns:
            dict: The evaluation result from the CorrectnessEvaluator.
        """
        return self._sdk_eval(query=query, response=response, ground_truth=ground_truth)

    def _to_async(self):
        """Convert the evaluator to an asynchronous version.

        Returns:
            An asynchronous version of the CorrectnessEvaluator.
        """
        return self._sdk_eval._to_async()
