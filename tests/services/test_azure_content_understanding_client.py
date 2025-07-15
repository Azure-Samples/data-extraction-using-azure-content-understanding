import unittest
from unittest.mock import patch, Mock
from requests.models import Response
from services.azure_content_understanding_client import AzureContentUnderstandingClient, _DEFAULT_API_VERSION


class TestAzureContentUnderstandingClientBase(unittest.TestCase):
    def setUp(self):
        """Set up the test case with a mock AzureContentUnderstandingClient."""
        self.endpoint = "https://example.com"
        self.subscription_key = "fake_subscription_key"
        self.client = AzureContentUnderstandingClient(
            endpoint=self.endpoint,
            subscription_key=self.subscription_key
        )


class TestGetAllAnalyzers(TestAzureContentUnderstandingClientBase):
    @patch("services.azure_content_understanding_client.requests.get")
    def test_get_all_analyzers(self, mock_get):
        """Test the get_all_analyzers method.

        Args:
            mock_get (Mock): The mock for the requests.get method.
        """
        # Arrange
        mock_response = Mock(spec=Response)
        mock_response.json.return_value = {"analyzers": []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Act
        result = self.client.get_all_analyzers()

        # Assert
        mock_get.assert_called_once_with(
            url=f"{self.endpoint}/contentunderstanding/analyzers?api-version={_DEFAULT_API_VERSION}",
            headers=self.client._headers,
            timeout=30
        )
        self.assertEqual(result, {"analyzers": []})


class TestGetAllClassifiers(TestAzureContentUnderstandingClientBase):
    @patch("services.azure_content_understanding_client.requests.get")
    def test_get_all_classifiers(self, mock_get):
        """Test the get_all_classifiers method.

        Args:
            mock_get (Mock): The mock for the requests.get method.
        """
        # Arrange
        mock_response = Mock(spec=Response)
        mock_response.json.return_value = {"classifiers": []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Act
        result = self.client.get_all_classifiers()

        # Assert
        mock_get.assert_called_once_with(
            url=f"{self.endpoint}/contentunderstanding/classifiers?api-version={_DEFAULT_API_VERSION}",
            headers=self.client._headers,
            timeout=30
        )
        self.assertEqual(result, {"classifiers": []})


class TestGetAnalyzerDetailById(TestAzureContentUnderstandingClientBase):
    @patch("services.azure_content_understanding_client.requests.get")
    def test_get_analyzer_detail_by_id(self, mock_get):
        """Test the get_analyzer_detail_by_id method.

        Args:
            mock_get (Mock): The mock for the requests.get method.
        """
        # Arrange
        analyzer_id = "analyzer_id"
        mock_response = Mock(spec=Response)
        mock_response.json.return_value = {"id": analyzer_id}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Act
        result = self.client.get_analyzer_detail_by_id(analyzer_id)

        # Assert
        mock_get.assert_called_once_with(
            url=f"{self.endpoint}/contentunderstanding/analyzers/{analyzer_id}?api-version={_DEFAULT_API_VERSION}",
            headers=self.client._headers,
            timeout=30
        )
        self.assertEqual(result, {"id": analyzer_id})


class TestGetClassifierDetailById(TestAzureContentUnderstandingClientBase):
    @patch("services.azure_content_understanding_client.requests.get")
    def test_get_classifier_detail_by_id(self, mock_get):
        """Test the get_classifier_detail_by_id method.

        Args:
            mock_get (Mock): The mock for the requests.get method.
        """
        # Arrange
        classifier_id = "classifier_id"
        mock_response = Mock(spec=Response)
        mock_response.json.return_value = {"id": classifier_id}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Act
        result = self.client.get_classifier_detail_by_id(classifier_id)

        # Assert
        mock_get.assert_called_once_with(
            url=f"{self.endpoint}/contentunderstanding/classifiers/{classifier_id}?api-version={_DEFAULT_API_VERSION}",
            headers=self.client._headers,
            timeout=30
        )
        self.assertEqual(result, {"id": classifier_id})


class TestBeginCreateAnalyzer(TestAzureContentUnderstandingClientBase):
    @patch("services.azure_content_understanding_client.requests.put")
    def test_begin_create_analyzer(self, mock_put):
        """Test the begin_create_analyzer method.

        Args:
            mock_put (Mock): The mock for the requests.put method.
        """
        # Arrange
        analyzer_id = "analyzer_id"
        analyzer_template = {"name": "test_analyzer"}
        mock_response = Mock(spec=Response)
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        # Act
        result = self.client.begin_create_analyzer(analyzer_id, analyzer_template)

        # Assert
        mock_put.assert_called_once_with(
            url=f"{self.endpoint}/contentunderstanding/analyzers/{analyzer_id}?api-version={_DEFAULT_API_VERSION}",
            headers={"Content-Type": "application/json", **self.client._headers},
            json=analyzer_template,
            timeout=30
        )
        self.assertEqual(result, mock_response)


class TestDeleteAnalyzer(TestAzureContentUnderstandingClientBase):
    @patch("services.azure_content_understanding_client.requests.delete")
    def test_delete_analyzer(self, mock_delete):
        """Test the delete_analyzer method.

        Args:
            mock_delete (Mock): The mock for the requests.delete method.
        """
        # Arrange
        analyzer_id = "analyzer_id"
        mock_response = Mock(spec=Response)
        mock_response.raise_for_status.return_value = None
        mock_delete.return_value = mock_response

        # Act
        result = self.client.delete_analyzer(analyzer_id)

        # Assert
        mock_delete.assert_called_once_with(
            url=f"{self.endpoint}/contentunderstanding/analyzers/{analyzer_id}?api-version={_DEFAULT_API_VERSION}",
            headers=self.client._headers,
            timeout=30
        )
        self.assertEqual(result, mock_response)


class TestBeginAnalyzeData(TestAzureContentUnderstandingClientBase):
    @patch("services.azure_content_understanding_client.requests.post")
    def test_begin_analyze_data(self, mock_post):
        """Test the begin_analyze_data method.

        Args:
            mock_post (Mock): The mock for the requests.post method.
        """
        # Arrange
        analyzer_id = "analyzer_id"
        data = b"test_data"
        mock_response = Mock(spec=Response)
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Act
        result = self.client.begin_analyze_data(analyzer_id, data)

        # Assert
        url = f"{self.endpoint}/contentunderstanding/analyzers/{analyzer_id}:analyze?api-version={_DEFAULT_API_VERSION}"
        mock_post.assert_called_once_with(
            url=url,
            headers={"Content-Type": "application/octet-stream", **self.client._headers},
            data=data,
            timeout=30
        )
        self.assertEqual(result, mock_response)


class TestBeginClassifyData(TestAzureContentUnderstandingClientBase):
    @patch("services.azure_content_understanding_client.requests.post")
    def test_begin_classify_data(self, mock_post):
        """Test the begin_classify_data method.

        Args:
            mock_post (Mock): The mock for the requests.post method.
        """
        # Arrange
        classifier_id = "classifier_id"
        data = b"test_data"
        mock_response = Mock(spec=Response)
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Act
        result = self.client.begin_classify_data(classifier_id, data)        # Assert
        url = (f"{self.endpoint}/contentunderstanding/classifiers/{classifier_id}:"
               f"classify?api-version={_DEFAULT_API_VERSION}")
        mock_post.assert_called_once_with(
            url=url,
            headers={"Content-Type": "application/octet-stream", **self.client._headers},
            data=data,
            timeout=30
        )
        self.assertEqual(result, mock_response)


class TestBeginClassifyFile(TestAzureContentUnderstandingClientBase):
    @patch("services.azure_content_understanding_client.requests.post")
    def test_begin_classify_file_with_url(self, mock_post):
        """Test the begin_classify_file method with URL.

        Args:
            mock_post (Mock): The mock for the requests.post method.
        """
        # Arrange
        classifier_id = "classifier_id"
        file_location = "https://example.com/file.pdf"
        mock_response = Mock(spec=Response)
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response        # Act
        result = self.client.begin_classify_file(classifier_id, file_location)

        # Assert
        url = (f"{self.endpoint}/contentunderstanding/classifiers/{classifier_id}:"
               f"classify?api-version={_DEFAULT_API_VERSION}")
        mock_post.assert_called_once_with(
            url=url,
            headers={"Content-Type": "application/json", **self.client._headers},
            data={"url": file_location},
            timeout=30
        )
        self.assertEqual(result, mock_response)

    @patch("builtins.open", create=True)
    @patch("services.azure_content_understanding_client.Path")
    @patch("services.azure_content_understanding_client.requests.post")
    def test_begin_classify_file_with_path(self, mock_post, mock_path, mock_open):
        """Test the begin_classify_file method with file path.

        Args:
            mock_post (Mock): The mock for the requests.post method.
            mock_path (Mock): The mock for the Path class.
            mock_open (Mock): The mock for the open function.
        """        # Arrange
        classifier_id = "classifier_id"
        file_location = "/path/to/file.pdf"
        file_data = b"test_file_data"

        mock_path.return_value.exists.return_value = True
        mock_file = Mock()
        mock_file.read.return_value = file_data
        mock_open.return_value.__enter__.return_value = mock_file

        mock_response = Mock(spec=Response)
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Act
        result = self.client.begin_classify_file(classifier_id, file_location)

        # Assert
        url = (f"{self.endpoint}/contentunderstanding/classifiers/{classifier_id}:"
               f"classify?api-version={_DEFAULT_API_VERSION}")
        mock_post.assert_called_once_with(
            url=url,
            headers={"Content-Type": "application/octet-stream", **self.client._headers},
            data=file_data,
            timeout=30
        )
        self.assertEqual(result, mock_response)

    def test_begin_classify_file_invalid_location(self):
        """Test the begin_classify_file method with invalid file location."""
        # Arrange
        classifier_id = "classifier_id"
        file_location = "invalid_location"

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            self.client.begin_classify_file(classifier_id, file_location)

        self.assertEqual(str(context.exception), "File location must be a valid path or URL.")


class TestPollResult(TestAzureContentUnderstandingClientBase):
    @patch("services.azure_content_understanding_client.requests.get")
    def test_poll_result(self, mock_get):
        """Test the poll_result method.

        Args:
            mock_get (Mock): The mock for the requests.get method.
        """
        # Arrange
        operation_location = "https://example.com/operation"
        mock_response = Mock(spec=Response)
        mock_response.headers = {"operation-location": operation_location}
        mock_response.json.return_value = {"status": "succeeded"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Act
        result = self.client.poll_result(mock_response)

        # Assert
        mock_get.assert_called_with(operation_location, headers=self.client._headers, timeout=30)
        self.assertEqual(result, {"status": "succeeded"})


class TestBeginCreateClassifier(TestAzureContentUnderstandingClientBase):
    @patch("services.azure_content_understanding_client.requests.put")
    def test_begin_create_classifier(self, mock_put):
        """Test the begin_create_classifier method.

        Args:
            mock_put (Mock): The mock for the requests.put method.
        """
        # Arrange
        classifier_id = "test_classifier_id"
        classifier_schema = {
            "description": "test classifier",
            "categories": {
                "category1": {"description": "test category"}
            }
        }
        mock_response = Mock(spec=Response)
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        # Act
        result = self.client.begin_create_classifier(classifier_id, classifier_schema)

        # Assert
        mock_put.assert_called_once_with(
            url=f"{self.endpoint}/contentunderstanding/classifiers/{classifier_id}?api-version={_DEFAULT_API_VERSION}",
            headers={"Content-Type": "application/json", **self.client._headers},
            json=classifier_schema,
            timeout=30
        )
        self.assertEqual(result, mock_response)


class TestDeleteClassifier(TestAzureContentUnderstandingClientBase):
    @patch("services.azure_content_understanding_client.requests.delete")
    def test_delete_classifier(self, mock_delete):
        """Test the delete_classifier method.

        Args:
            mock_delete (Mock): The mock for the requests.delete method.
        """
        # Arrange
        classifier_id = "test_classifier_id"
        mock_response = Mock(spec=Response)
        mock_response.raise_for_status.return_value = None
        mock_delete.return_value = mock_response

        # Act
        result = self.client.delete_classifier(classifier_id)

        # Assert
        mock_delete.assert_called_once_with(
            url=f"{self.endpoint}/contentunderstanding/classifiers/{classifier_id}?api-version={_DEFAULT_API_VERSION}",
            headers=self.client._headers,
            timeout=30
        )
        self.assertEqual(result, mock_response)
