import psycopg2


class DBConnection:
    """Singleton-обёртка над psycopg2.connect."""

    __instance = None

    def __new__(cls, db_config: dict = None):
        if cls.__instance is None:
            if db_config is None:
                raise ValueError(
                    "При первом создании подключения необходимо передать db_config."
                )
            instance = super().__new__(cls)
            instance._config = dict(db_config)
            instance.connection = None
            instance._open()
            cls.__instance = instance
        elif db_config is not None and cls.__instance._config != db_config:
            raise RuntimeError(
                "DBConnection уже сконфигурирован другой базой. "
                "Для пересоздания вызовите DBConnection.reset()."
            )
        return cls.__instance

    def _open(self):
        self.connection = psycopg2.connect(**self._config)
        self.connection.autocommit = True

    def get_connection(self):
        if self.connection is None or self.connection.closed:
            self._open()
        return self.connection

    def close(self):
        if self.connection is not None and not self.connection.closed:
            self.connection.close()

    @classmethod
    def reset(cls):
        """Сбрасывает Singleton (для тестов)."""
        if cls.__instance is not None:
            cls.__instance.close()
            cls.__instance = None
