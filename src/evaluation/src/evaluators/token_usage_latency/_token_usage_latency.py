from pydantic import BaseModel


class QueryMetrics(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    total_latency_sec: float


class TokenUsageLatencyEvaluator:
    """Evaluator that records the token usage and latency of a particular query response."""
    def __init__(self):
        """Initializes the TokenUsageLatencyEvaluator."""
        pass

    def __call__(self, *, metrics: str, **kwargs):
        """Returns the token usage and latency from the metrics part of the response body.

        Args:
            metrics (str): Stringified metrics from query response
            **kwargs: Additional keyword arguments.

        Returns:
            dict: A dictionary containing the token usage (prompt, completions, and total)
                  and the total query latency.
        """
        metrics_obj = QueryMetrics.model_validate_json(metrics)
        return metrics_obj.model_dump()
