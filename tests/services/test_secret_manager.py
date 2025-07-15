from unittest import TestCase
from unittest.mock import MagicMock
from services.secret_manager import SecretManager
from utils import Singleton


class TestGetSecretValue(TestCase):
    def test_happy_path(self):
        """Test get_secret_value."""
        # arrange
        mock_secret_client = MagicMock()
        mock_secret_client.get_secret.return_value.value = "bar"
        Singleton._instances.clear()
        secret_manager = SecretManager(mock_secret_client)

        # act
        secret_value = secret_manager.get_secret_value("foo")

        # assert
        assert secret_value == "bar"
