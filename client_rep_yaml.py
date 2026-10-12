import os

import yaml

from client import Client
from repository_base import ClientRepositoryBase


class Client_rep_yaml(ClientRepositoryBase):
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        self.read_from_file()

    def read_from_file(self):
        if not os.path.exists(self.file_path):
            self.clients = []
            return
        with open(self.file_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or []
            if not isinstance(data, list):
                raise ValueError("YAML-файл должен содержать список объектов клиентов.")
            self.clients = [Client(item) for item in data]

    def write_to_file(self):
        with open(self.file_path, "w", encoding="utf-8") as file:
            data = [
                {
                    "client_id": client.client_id,
                    "last_name": client.last_name,
                    "first_name": client.first_name,
                    "passport_data": client.passport_data,
                    "phone_number": client.phone_number,
                }
                for client in self.clients
            ]
            yaml.dump(data, file, allow_unicode=True, sort_keys=False)
