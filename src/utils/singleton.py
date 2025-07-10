class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        """Creates a singleton instance of the class.

        Args:
            cls: The class to create a singleton instance of.
            *args: Positional arguments for the class constructor
            **kwargs: Keyword arguments for the class constructor

        Returns:
            Singleton: The singleton instance.
        """
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls) \
                .__call__(*args, **kwargs)
        return cls._instances[cls]
