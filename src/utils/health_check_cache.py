import time


class HealthCheckCache:
    last_checked: int = 0
    unhealthy_services: list | None = None
    ttl: int

    def __init__(self, ttl: int = 300):
        """Initialize the HealthCheckCache with a time-to-live (TTL).

        Args:
            ttl (int): The time-to-live duration in seconds for the cache.
        """
        self.ttl = ttl

    def is_cache_valid(self):
        current_time = time.time()
        return (current_time - self.last_checked) < self.ttl

    def update_time(self):
        self.last_checked = time.time()

    def set_unhealthy_services(self, unhealthy_services: list | None):
        self.unhealthy_services = unhealthy_services

    @property
    def is_healthy(self):
        return self.unhealthy_services is None or len(self.unhealthy_services) == 0

    @property
    def error_message(self) -> str | None:
        if not self.is_healthy:
            unhealthy_service_names = [elem["name"] for elem in self.unhealthy_services]
            return f"The following services are unhealthy: {', '.join(unhealthy_service_names)}"
        return None


health_check_cache = HealthCheckCache()
service_status = {
    "openai": None
}
