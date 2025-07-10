def build_config_id(
    name: str,
    version: str,
):
    """Builds a config ID from the name and version.

    Args:
        name (str): The name of the config.
        version (str): The version of the config.

    Returns:
        str: The config ID.
    """
    return f"{name}-{version}"
