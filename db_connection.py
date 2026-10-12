import psycopg2


class DBConnection:
    __instance = None

    def __new__(cls, db_config: dict = None):
        if cls.__instance is None:
            if db_config is None:
                raise ValueError(
                    "При первом создании подключения необходимо передать db_config."
                )
            instance = super().__new__(cls)
            instance._config = dict(db_config)
            instance.connection = psycopg2.connect(**instance._config)
            instance.connection.autocommit = True
            cls.__instance = instance
        return cls.__instance

    def get_connection(self):
        if self.connection is None or self.connection.closed:
            self.connection = psycopg2.connect(**self._config)
            self.connection.autocommit = True
        return self.connection

    def close(self):
        if self.connection is not None and not self.connection.closed:
            self.connection.close()
