import logging
from services.azure_content_understanding_client import AzureContentUnderstandingClient
from models.http_error import HTTPError


class ClassifierController(object):
    """Controller for managing Azure Content Understanding classifiers."""

    _azure_content_understanding_client: AzureContentUnderstandingClient

    def __init__(self, azure_content_understanding_client: AzureContentUnderstandingClient):
        """Initializes the ClassifierController.

        Args:
            azure_content_understanding_client (AzureContentUnderstandingClient):
                The client used for interacting with Azure Content Understanding services.
        """
        self._azure_content_understanding_client = azure_content_understanding_client

    def create_classifier(self, classifier_id: str, classifier_schema: dict) -> dict:
        """Creates a new classifier with the provided schema.

        Args:
            classifier_id (str): The unique identifier for the classifier.
            classifier_schema (dict): The JSON schema definition for the classifier.

        Returns:
            dict: Success response with classifier creation status.

        Raises:
            HTTPError: If the classifier creation fails.
        """
        try:
            logging.info(f"Creating classifier with ID: {classifier_id}...")
            resp = self._azure_content_understanding_client.begin_create_classifier(
                classifier_id, classifier_schema
            )
            # Poll the operation result to ensure classifier is fully created
            self._azure_content_understanding_client.poll_result(resp)
            logging.info(f"Classifier {classifier_id} created successfully")
            return {
                "message": f"Classifier '{classifier_id}' created successfully",
                "classifier_id": classifier_id,
                "status": "created"
            }
        except Exception as e:
            logging.error(f"Failed to create classifier {classifier_id}: {str(e)}")
            raise HTTPError(f"Failed to create classifier: {str(e)}", 500)

    def get_classifier(self, classifier_id: str) -> dict:
        """Retrieves a classifier by its ID.

        Args:
            classifier_id (str): The unique identifier for the classifier.

        Returns:
            dict: The classifier configuration and details.

        Raises:
            HTTPError: If the classifier is not found or retrieval fails.
        """
        try:
            classifier_data = self._azure_content_understanding_client.get_classifier_detail_by_id(
                classifier_id
            )
            logging.info(f"Retrieved classifier {classifier_id}")
            return classifier_data
        except Exception as e:
            logging.error(f"Failed to retrieve classifier {classifier_id}: {str(e)}")

            if "404" in str(e) or "not found" in str(e).lower():
                raise HTTPError(f"Classifier '{classifier_id}' not found", 404)
            raise HTTPError(f"Failed to retrieve classifier: {str(e)}", 500)
