import base64
import json


def decode_bearer_token(bearer_token: str):
    """Returns the data from the bearer token.

    Args:
        bearer_token (str): The bearer token to deconstruct.

    Returns:
        dict: A dictionary containing the data from the bearer token.
    """
    # Split the token into its components
    components = bearer_token.split(".")

    # Decode the payload
    payload = base64.urlsafe_b64decode(components[1] + "==").decode("utf-8")

    # Parse the JSON payload
    payload_json = json.loads(payload)

    return payload_json
