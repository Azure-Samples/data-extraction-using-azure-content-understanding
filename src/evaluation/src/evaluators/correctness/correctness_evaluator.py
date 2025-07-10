import os
import math
from typing import Dict, Union

from typing_extensions import overload, override

from azure.ai.evaluation._exceptions import (
    EvaluationException,
    ErrorBlame,
    ErrorCategory,
    ErrorTarget
)
from azure.ai.evaluation._evaluators._common import PromptyEvaluatorBase
from azure.ai.evaluation._common.utils import (
    parse_quality_evaluator_reason_score
)


class CorrectnessEvaluator(PromptyEvaluatorBase):
    """Evaluates correctness score for a given query, response, and ground-truth answer, including reasoning.

    The correctness measure assesses the accuracy of an AI-generated response by comparing it against a ground-truth
    answer. This ensures that the response aligns with the expected answer and meets the desired level of correctness.
    Use the correctness metric when you need to verify that AI-generated responses are factually accurate and match
    the ground-truth answer.

    Correctness scores range from 1 to 5, with 1 being the least correct and 5 being the most correct.

    :param model_config: Configuration for the Azure OpenAI model.
    :type model_config: Union[~azure.ai.evaluation.AzureOpenAIModelConfiguration,
        ~azure.ai.evaluation.OpenAIModelConfiguration]

    .. admonition:: Example:

        .. literalinclude:: ../samples/evaluation_samples_evaluate.py
            :start-after: [START correctness_evaluator]
            :end-before: [END correctness_evaluator]
            :language: python
            :dedent: 8
            :caption: Initialize and call a CorrectnessEvaluator.

    .. note::

        To align with our support of a diverse set of models, an output key without the `gpt_` prefix has been added.
        To maintain backwards compatibility, the old key with the `gpt_` prefix is still present in the output;
        however, it is recommended to use the new key moving forward as the old key will be deprecated in the future.
    """

    _PROMPTY_FILE = "correctness.prompty"
    _RESULT_KEY = "correctness"

    """Evaluator identifier, experimental and to be used only with evaluation in cloud."""

    @override
    def __init__(self, model_config: dict):
        """Initialize CorrectnessEvaluator with the given model configuration."""
        current_dir = os.path.dirname(__file__)
        prompty_path = os.path.join(current_dir, self._PROMPTY_FILE)  # Default to no query
        super().__init__(model_config=model_config, prompty_file=prompty_path, result_key=self._RESULT_KEY)

    @overload
    def __call__(
        self,
        *,
        query: str,
        response: str,
        ground_truth: str,
    ) -> Dict[str, Union[str, float]]:
        ...

    @override
    def __call__(  # pylint: disable=docstring-missing-param
        self,
        *args,
        **kwargs,
    ):
        """Evaluate correctness for a given query, response, and ground-truth answer.

        :keyword query: The query to be evaluated.
        :paramtype query: str
        :keyword response: The response to be evaluated.
        :paramtype response: str
        :keyword ground_truth: The ground-truth answer to compare against.
        :paramtype ground_truth: str
        :return: The correctness score.
        :rtype: Dict[str, Union[str, float]]
        """
        return super().__call__(*args, **kwargs)

    @override
    async def _do_eval(self, eval_input: Dict[str, Union[str, float]]):
        """Do a relevance evaluation.

        :param eval_input: The input to the evaluator. Expected to contain
        whatever inputs are needed for the _flow method, including context
        and other fields depending on the child class.
        :type eval_input: Dict[str, Union[str, float]]
        :return: The evaluation result.
        :rtype: Dict[str, Union[str, float]]
        """
        if "query" not in eval_input and "response" not in eval_input:
            raise EvaluationException(
                message="Only text conversation inputs are supported.",
                internal_message="Only text conversation inputs are supported.",
                blame=ErrorBlame.USER_ERROR,
                category=ErrorCategory.INVALID_VALUE,
                target=ErrorTarget.CONVERSATION,
            )
        llm_output = await self._flow(timeout=self._LLM_CALL_TIMEOUT, **eval_input)

        score = math.nan
        if llm_output:
            score, reason = parse_quality_evaluator_reason_score(llm_output)
            return {
                self._result_key: float(score),
                f"{self._result_key}_reason": reason,
            }
        return {self._result_key: float(score)}
