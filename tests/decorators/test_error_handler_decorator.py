import unittest
from azure.functions import HttpResponse
from models import HTTPError
from decorators.error_handler_decorator import error_handler


class TestErrorHandler(unittest.TestCase):
    """Test the error_handler."""

    def test_happy_path(self):
        """Test the happy path of the error_handler decorator."""
        @error_handler
        def sample_function():
            return HttpResponse("Success", status_code=200)

        result = sample_function()
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.get_body().decode(), "Success")

    def test_error_handler(self):
        """Test the error_handler decorator."""
        @error_handler
        def sample_function():
            raise Exception("This is a test exception")

        with self.assertRaises(Exception) as context:
            sample_function()
        self.assertEqual(str(context.exception), "This is a test exception")

    def test_http_error(self):
        """Test the HTTPError exception in the error_handler decorator."""
        @error_handler
        def sample_function():
            raise HTTPError("This is a test HTTPError", 400)

        result: HttpResponse = sample_function()
        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.get_body().decode(), "This is a test HTTPError")
