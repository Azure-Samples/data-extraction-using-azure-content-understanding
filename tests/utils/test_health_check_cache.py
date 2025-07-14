import unittest
import time
from utils.health_check_cache import HealthCheckCache


class TestHealthCheckCache(unittest.TestCase):
    """Unit tests for the HealthCheckCache class."""

    def setUp(self):
        """Set up a HealthCheckCache instance for testing."""
        self.cache = HealthCheckCache(ttl=300)

    def test_is_cache_valid_initially_invalid(self):
        """Test that the cache is initially invalid."""
        self.assertFalse(self.cache.is_cache_valid())

    def test_update_time_makes_cache_valid(self):
        """Test that updating the time makes the cache valid."""
        self.cache.update_time()
        self.assertTrue(self.cache.is_cache_valid())

    def test_cache_expires_after_ttl(self):
        """Test that the cache becomes invalid after the TTL expires."""
        self.cache.update_time()
        time.sleep(1)  # Simulate time passing
        self.cache.ttl = 0  # Set TTL to 0 to force expiration
        self.assertFalse(self.cache.is_cache_valid())

    def test_set_unhealthy_services(self):
        """Test setting unhealthy services."""
        self.cache.set_unhealthy_services([{"name": "service1", "message": "error"}])
        self.assertEqual(self.cache.unhealthy_services, [{"name": "service1", "message": "error"}])

    def test_is_healthy_with_no_unhealthy_services(self):
        """Test that the cache is healthy when there are no unhealthy services."""
        self.cache.set_unhealthy_services(None)
        self.assertTrue(self.cache.is_healthy)

    def test_is_healthy_with_unhealthy_services(self):
        """Test that the cache is unhealthy when there are unhealthy services."""
        self.cache.set_unhealthy_services([{"name": "service1", "message": "error"}])
        self.assertFalse(self.cache.is_healthy)

    def test_error_message_with_unhealthy_services(self):
        """Test the error message when there are unhealthy services."""
        self.cache.set_unhealthy_services([{"name": "service1", "message": "error"}])
        self.assertEqual(
            self.cache.error_message,
            "The following services are unhealthy: service1"
        )

    def test_error_message_with_no_unhealthy_services(self):
        """Test the error message when there are no unhealthy services."""
        self.cache.set_unhealthy_services(None)
        self.assertIsNone(self.cache.error_message)
