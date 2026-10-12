from client import Client
from client_rep_db import Client_rep_DB
from repository_base import ClientRepositoryBase


class Client_rep_DB_Adapter(ClientRepositoryBase):
    """Делегирует CRUD-операции в Client_rep_DB."""

    def __init__(self, db_repository: Client_rep_DB):
        self.adaptee = db_repository

    def get_all(self) -> list:
        return self.adaptee.get_all()

    def get_by_id(self, client_id: int) -> Client:
        return self.adaptee.get_by_id(client_id)

    def get_k_n_short_list(self, k: int, n: int) -> list:
        return self.adaptee.get_k_n_short_list(k, n)

    def get_page_short(
        self,
        k: int,
        n: int,
        where_sql: str = "",
        where_params: tuple = (),
        order_sql: str = "",
    ) -> list:
        return self.adaptee.get_page_short(
            k, n, where_sql, where_params, order_sql
        )

    def get_filtered_count(
        self, where_sql: str = "", where_params: tuple = ()
    ) -> int:
        return self.adaptee.get_filtered_count(where_sql, where_params)

    def add(self, client: Client):
        self.adaptee.add(client)

    def update(self, client_id: int, new_client: Client):
        self.adaptee.update(client_id, new_client)

    def delete(self, client_id: int):
        self.adaptee.delete(client_id)

    def get_count(self) -> int:
        return self.adaptee.get_count()
