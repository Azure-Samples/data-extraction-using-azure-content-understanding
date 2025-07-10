class HTTPError(Exception):
    def __init__(self, message: str, status_code: int):
        """Initializes the HTTPError with a message and status code.

        Args:
            message (str): The error message.
            status_code (int): The HTTP status code.
        """
        super().__init__(message)
        self.status_code = status_code
