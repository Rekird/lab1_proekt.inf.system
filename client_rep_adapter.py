from client import Client
from client_rep_db import Client_rep_DB
from repository_base import ClientRepositoryBase


class Client_rep_DB_Adapter(ClientRepositoryBase):
    """Встраивает Client_rep_DB в общую иерархию ClientRepositoryBase."""

    def __init__(self, db_repository: Client_rep_DB):
        super().__init__()
        self.adaptee = db_repository

    def read_from_file(self):
        raise NotImplementedError("Чтение из файла не применимо к репозиторию БД.")

    def write_to_file(self):
        raise NotImplementedError("Запись в файл не применима к репозиторию БД.")

    def get_all(self) -> list:
        return self.adaptee.get_all()

    def get_by_id(self, client_id: int) -> Client:
        return self.adaptee.get_by_id(client_id)

    def get_k_n_short_list(self, k: int, n: int) -> list:
        return self.adaptee.get_k_n_short_list(k, n)

    def sort_by_last_name(self):
        raise NotImplementedError(
            "Сортировка списка в памяти не применима к репозиторию БД. "
            "Используйте декоратор с параметром sort_by."
        )

    def add(self, client: Client):
        self.adaptee.add(client)

    def update(self, client_id: int, new_client: Client):
        self.adaptee.update(client_id, new_client)

    def delete(self, client_id: int):
        self.adaptee.delete(client_id)

    def get_count(self) -> int:
        return self.adaptee.get_count()
