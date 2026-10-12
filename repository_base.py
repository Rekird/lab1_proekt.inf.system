from client import Client, ClientMapper


class ClientRepositoryBase:
    """Общий базовый класс файловых репозиториев и адаптера БД."""

    def __init__(self):
        self.clients = []

    def read_from_file(self):
        raise NotImplementedError("Метод должен быть реализован в классе-наследнике")

    def write_to_file(self):
        raise NotImplementedError("Метод должен быть реализован в классе-наследнике")

    def get_all(self) -> list:
        return list(self.clients)

    def get_by_id(self, client_id: int) -> Client:
        for client in self.clients:
            if client.client_id == client_id:
                return client
        raise ValueError(f"Клиент с ID {client_id} не найден.")

    def get_k_n_short_list(self, k: int, n: int) -> list:
        self._validate_page(k, n)
        start = (n - 1) * k
        end = start + k
        slice_clients = self.clients[start:end]
        return [ClientMapper.short_version(client) for client in slice_clients]

    def sort_by_last_name(self):
        self.clients.sort(key=lambda client: client.last_name)

    def add(self, client: Client):
        new_id = max([item.client_id for item in self.clients], default=0) + 1
        client.client_id = new_id
        self.clients.append(client)

    def update(self, client_id: int, new_client: Client):
        for index, client in enumerate(self.clients):
            if client.client_id == client_id:
                new_client.client_id = client_id
                self.clients[index] = new_client
                return
        raise ValueError(f"Клиент с ID {client_id} не найден.")

    def delete(self, client_id: int):
        original_count = len(self.clients)
        self.clients = [
            client for client in self.clients if client.client_id != client_id
        ]
        if len(self.clients) == original_count:
            raise ValueError(f"Клиент с ID {client_id} не найден.")

    def get_count(self) -> int:
        return len(self.clients)

    @staticmethod
    def _validate_page(k: int, n: int):
        if not isinstance(k, int) or isinstance(k, bool) or k <= 0:
            raise ValueError("Размер страницы k должен быть положительным целым числом.")
        if not isinstance(n, int) or isinstance(n, bool) or n <= 0:
            raise ValueError("Номер страницы n должен быть положительным целым числом.")
