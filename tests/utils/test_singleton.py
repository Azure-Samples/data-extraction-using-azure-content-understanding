from unittest import TestCase
from utils.singleton import Singleton


class TestSingleton(TestCase):
    def test_happy_path(self):
        """Test singleton behavior."""
        class TestClass(metaclass=Singleton):
            pass

        instance1 = TestClass()
        instance2 = TestClass()

        assert instance1 is instance2
