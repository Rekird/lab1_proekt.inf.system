from client import Client, ClientMapper
from repository_base import ClientRepositoryBase


class ClientRepositoryDecorator(ClientRepositoryBase):
    def __init__(self, wrapped_repo: ClientRepositoryBase):
        super().__init__()
        self._wrapped = wrapped_repo

    def read_from_file(self):
        return self._wrapped.read_from_file()

    def write_to_file(self):
        return self._wrapped.write_to_file()

    def get_all(self) -> list:
        return self._wrapped.get_all()

    def get_by_id(self, client_id: int) -> Client:
        return self._wrapped.get_by_id(client_id)

    def get_k_n_short_list(self, k: int, n: int) -> list:
        return self._wrapped.get_k_n_short_list(k, n)

    def sort_by_last_name(self):
        return self._wrapped.sort_by_last_name()

    def add(self, client: Client):
        self._wrapped.add(client)

    def update(self, client_id: int, new_client: Client):
        self._wrapped.update(client_id, new_client)

    def delete(self, client_id: int):
        self._wrapped.delete(client_id)

    def get_count(self) -> int:
        return self._wrapped.get_count()


class ClientRepositoryFilterSortDecorator(ClientRepositoryDecorator):
    """Добавляет фильтр и способ сортировки в get_k_n_short_list и get_count."""

    ALLOWED_SORT_FIELDS = {
        "last_name",
        "first_name",
        "phone_number",
        "passport_data",
        "client_id",
    }

    def get_k_n_short_list(
        self, k: int, n: int, filter_by=None, sort_by=None, reverse: bool = False
    ) -> list:
        ClientRepositoryBase._validate_page(k, n)
        clients = self._apply_filter_sort(self.get_all(), filter_by, sort_by, reverse)
        start = (n - 1) * k
        page = clients[start : start + k]
        return [ClientMapper.short_version(client) for client in page]

    def get_count(self, filter_by=None, sort_by=None, reverse: bool = False) -> int:
        clients = self._apply_filter_sort(self.get_all(), filter_by, sort_by, reverse)
        return len(clients)

    def _apply_filter_sort(self, clients, filter_by, sort_by, reverse: bool) -> list:
        filtered = list(clients)

        if filter_by is not None:
            if callable(filter_by):
                filtered = [client for client in filtered if filter_by(client)]
            elif isinstance(filter_by, dict):
                filtered = [
                    client
                    for client in filtered
                    if self._matches_dict(client, filter_by)
                ]
            else:
                raise TypeError("filter_by должен быть функцией или словарём условий.")

        if sort_by is not None:
            if callable(sort_by):
                filtered.sort(key=sort_by, reverse=reverse)
            elif isinstance(sort_by, str):
                if sort_by not in self.ALLOWED_SORT_FIELDS:
                    raise ValueError(
                        f"Недопустимое поле сортировки: {sort_by}. "
                        f"Допустимы: {', '.join(sorted(self.ALLOWED_SORT_FIELDS))}."
                    )
                filtered.sort(
                    key=lambda client: getattr(client, sort_by), reverse=reverse
                )
            else:
                raise TypeError("sort_by должен быть именем поля или функцией.")

        return filtered

    @staticmethod
    def _matches_dict(client: Client, conditions: dict) -> bool:
        for field_name, expected in conditions.items():
            if not hasattr(client, field_name):
                raise ValueError(f"У клиента нет поля '{field_name}'.")
            if getattr(client, field_name) != expected:
                return False
        return True
