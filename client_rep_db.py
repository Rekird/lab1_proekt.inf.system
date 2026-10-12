from client import Client, ClientMapper
from db_connection import DBConnection
from repository_base import ClientRepositoryBase


class Client_rep_DB:
    def __init__(self, db_config: dict = None):
        self.db_manager = DBConnection(db_config)

    def get_by_id(self, client_id: int) -> Client:
        with self.db_manager.get_connection().cursor() as cursor:
            cursor.execute(
                "SELECT id, last_name, first_name, passport_data, phone_number "
                "FROM clients WHERE id = %s;",
                (client_id,),
            )
            row = cursor.fetchone()
            if row is None:
                raise ValueError(f"Клиент с ID {client_id} не найден.")
            return Client(row[0], row[1], row[2], row[3], row[4])

    def get_all(self) -> list:
        with self.db_manager.get_connection().cursor() as cursor:
            cursor.execute(
                "SELECT id, last_name, first_name, passport_data, phone_number "
                "FROM clients ORDER BY id;"
            )
            rows = cursor.fetchall()
            return [Client(row[0], row[1], row[2], row[3], row[4]) for row in rows]

    def get_k_n_short_list(self, k: int, n: int) -> list:
        ClientRepositoryBase._validate_page(k, n)
        with self.db_manager.get_connection().cursor() as cursor:
            offset = (n - 1) * k
            cursor.execute(
                "SELECT id, last_name, first_name, passport_data, phone_number "
                "FROM clients ORDER BY id LIMIT %s OFFSET %s;",
                (k, offset),
            )
            rows = cursor.fetchall()
            clients = [Client(row[0], row[1], row[2], row[3], row[4]) for row in rows]
            return [ClientMapper.short_version(client) for client in clients]

    def add(self, client: Client):
        with self.db_manager.get_connection().cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO clients (last_name, first_name, passport_data, phone_number)
                VALUES (%s, %s, %s, %s) RETURNING id;
                """,
                (
                    client.last_name,
                    client.first_name,
                    client.passport_data,
                    client.phone_number,
                ),
            )
            client.client_id = cursor.fetchone()[0]

    def update(self, client_id: int, new_client: Client):
        with self.db_manager.get_connection().cursor() as cursor:
            cursor.execute(
                """
                UPDATE clients
                SET last_name = %s, first_name = %s, passport_data = %s, phone_number = %s
                WHERE id = %s;
                """,
                (
                    new_client.last_name,
                    new_client.first_name,
                    new_client.passport_data,
                    new_client.phone_number,
                    client_id,
                ),
            )
            if cursor.rowcount == 0:
                raise ValueError(f"Клиент с ID {client_id} не найден.")

    def delete(self, client_id: int):
        with self.db_manager.get_connection().cursor() as cursor:
            cursor.execute("DELETE FROM clients WHERE id = %s;", (client_id,))
            if cursor.rowcount == 0:
                raise ValueError(f"Клиент с ID {client_id} не найден.")

    def get_count(self) -> int:
        with self.db_manager.get_connection().cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM clients;")
            return cursor.fetchone()[0]
