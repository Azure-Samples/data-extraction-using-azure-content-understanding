import json
import unittest
from unittest.mock import AsyncMock, patch
from azure.functions import HttpRequest
from routes.api.v1.health_check_routes import startup, health_check


class TestHealthCheckRoutes(unittest.TestCase):
    """Unit tests for health check routes."""

    async def test_startup(self):
        """Test the startup route."""
        req = HttpRequest(method="GET", url="/v1/startup", body=None)

        response = await startup(req)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        self.assertEqual(
            json.loads(response.get_body().decode()),
            {"status": "healthy", "details": "Function App is running."}
        )

    @patch("routes.api.v1.health_check_routes.HealthCheckController.perform_health_checks", new_callable=AsyncMock)
    @patch("routes.api.v1.health_check_routes.get_app_config_manager")
    async def test_health_check_healthy(self, mock_get_app_config_manager, mock_perform_health_checks):
        """Test the health check route when the status is healthy."""
        mock_get_app_config_manager.return_value.hydrate_config.return_value = {}
        mock_perform_health_checks.return_value = {"status": "healthy", "checks": {}}

        req = HttpRequest(method="GET", url="/v1/health", body=None)

        response = await health_check(req)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        self.assertEqual(
            json.loads(response.get_body().decode()),
            {"status": "healthy", "checks": {}}
        )

    @patch("routes.api.v1.health_check_routes.HealthCheckController.perform_health_checks", new_callable=AsyncMock)
    @patch("routes.api.v1.health_check_routes.get_app_config_manager")
    async def test_health_check_unhealthy(self, mock_get_app_config_manager, mock_perform_health_checks):
        """Test the health check route when the status is unhealthy."""
        mock_get_app_config_manager.return_value.hydrate_config.return_value = {}
        mock_perform_health_checks.return_value = {
            "status": "unhealthy",
            "checks": {"cosmos_db": {"status": "unhealthy", "details": "Connection error"}}
        }

        req = HttpRequest(method="GET", url="/v1/health", body=None)

        response = await health_check(req)

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        self.assertEqual(
            json.loads(response.get_body().decode()),
            {
                "status": "unhealthy",
                "checks": {"cosmos_db": {"status": "unhealthy", "details": "Connection error"}}
            }
        )
