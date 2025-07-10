from .app_config_manager import get_app_config_manager


class LlmConfig:
    _key: str
    _endpoint: str
    _api_version: str
    _default_model: str

    def __init__(self):
        """LLM cconfig constructor."""
        config = get_app_config_manager().hydrate_config()

        default_model = config.llm.model_name.value
        endpoint = config.llm.endpoint.value
        key = config.llm.access_key.value
        api_version = config.llm.api_version.value

        if not key or not endpoint or not api_version or not default_model:
            raise ValueError("Invalid LLM configuration")

        self._key = key
        self._endpoint = endpoint
        self._api_version = api_version
        self._default_model = default_model

    @property
    def key(self):
        return self._key

    @property
    def endpoint(self):
        return self._endpoint

    @property
    def api_version(self):
        return self._api_version

    @property
    def default_model(self):
        return self._default_model


llm_config: LlmConfig | None = None


def get_llm_config() -> LlmConfig:
    """Get LLM config as singleton."""
    global llm_config
    if not llm_config:
        llm_config = LlmConfig()
    return llm_config
