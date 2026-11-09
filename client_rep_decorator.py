from client import Client, ClientMapper
from repository_base import ClientRepositoryBase


class ClientRepositoryDecorator(ClientRepositoryBase):
    def __init__(self, wrapped_repo: ClientRepositoryBase):
        self._wrapped = wrapped_repo

    def get_all(self) -> list:
        return self._wrapped.get_all()

    def get_by_id(self, client_id: int) -> Client:
        return self._wrapped.get_by_id(client_id)

    def get_k_n_short_list(self, k: int, n: int) -> list:
        return self._wrapped.get_k_n_short_list(k, n)

    def add(self, client: Client):
        self._wrapped.add(client)

    def update(self, client_id: int, new_client: Client):
        self._wrapped.update(client_id, new_client)

    def delete(self, client_id: int):
        self._wrapped.delete(client_id)

    def get_count(self) -> int:
        return self._wrapped.get_count()

    @staticmethod
    def _filter_sort_in_memory(clients, filter_by, sort_by, reverse) -> list:
        filtered = list(clients)

        if filter_by is not None:
            if callable(filter_by):
                filtered = [c for c in filtered if filter_by(c)]
            elif isinstance(filter_by, dict):
                filtered = [
                    c for c in filtered if ClientRepositoryDecorator._matches_dict(c, filter_by)
                ]
            else:
                raise TypeError(
                    "filter_by должен быть функцией или словарём условий."
                )

        if sort_by is not None:
            if callable(sort_by):
                filtered.sort(key=sort_by, reverse=reverse)
            elif isinstance(sort_by, str):
                filtered.sort(key=lambda c: getattr(c, sort_by), reverse=reverse)
            else:
                raise TypeError(
                    "sort_by должен быть именем поля или функцией."
                )

        return filtered

    @staticmethod
    def _matches_dict(client: Client, conditions: dict) -> bool:
        for field_name, expected in conditions.items():
            if not hasattr(client, field_name):
                raise ValueError(f"У клиента нет поля '{field_name}'.")
            if getattr(client, field_name) != expected:
                return False
        return True


class ClientRepositoryFilterSortDecorator(ClientRepositoryDecorator):
    """Фильтр/сортировка для файловых репозиториев (get_all + Python)."""

    ALLOWED_SORT_FIELDS = {
        "last_name",
        "first_name",
        "phone_number",
        "passport_data",
        "client_id",
    }

    def get_k_n_short_list(
        self, k: int, n: int, filter_by=None, sort_by=None, reverse=False
    ) -> list:
        ClientRepositoryBase._validate_page(k, n)
        self._validate(filter_by, sort_by)
        clients = self._filter_sort_in_memory(
            self.get_all(), filter_by, sort_by, reverse
        )
        start = (n - 1) * k
        page = clients[start : start + k]
        return [ClientMapper.short_version(client) for client in page]

    def get_count(
        self, filter_by=None, sort_by=None, reverse=False
    ) -> int:
        self._validate(filter_by, sort_by)
        clients = self._filter_sort_in_memory(
            self.get_all(), filter_by, sort_by, reverse
        )
        return len(clients)

    def _validate(self, filter_by, sort_by):
        if isinstance(sort_by, str) and sort_by not in self.ALLOWED_SORT_FIELDS:
            raise ValueError(
                f"Недопустимое поле сортировки: {sort_by}. "
                f"Допустимы: {', '.join(sorted(self.ALLOWED_SORT_FIELDS))}."
            )
        if isinstance(filter_by, dict):
            for field_name in filter_by:
                if field_name not in self.ALLOWED_SORT_FIELDS:
                    raise ValueError(
                        f"Недопустимое поле фильтра: {field_name}. "
                        f"Допустимы: "
                        f"{', '.join(sorted(self.ALLOWED_SORT_FIELDS))}."
                    )


class ClientRepositoryDBSortFilterDecorator(ClientRepositoryDecorator):
    """Фильтр/сортировка для репозитория на БД (WHERE/ORDER BY в SQL)."""

    ALLOWED_SORT_FIELDS = {
        "last_name",
        "first_name",
        "phone_number",
        "passport_data",
        "client_id",
    }

    COLUMN_MAP = {
        "last_name": "last_name",
        "first_name": "first_name",
        "phone_number": "phone_number",
        "passport_data": "passport_data",
        "client_id": "id",
    }

    def get_k_n_short_list(
        self,
        k: int,
        n: int,
        filter_by=None,
        sort_by=None,
        reverse: bool = False,
    ) -> list:
        ClientRepositoryBase._validate_page(k, n)

        # Произвольную Python-функцию в SQL не переложить — считаем в памяти.
        if callable(filter_by):
            clients = self._filter_sort_in_memory(
                self.get_all(), filter_by, sort_by, reverse
            )
            start = (n - 1) * k
            page = clients[start : start + k]
            return [ClientMapper.short_version(client) for client in page]

        where_sql, where_params = self._build_where(filter_by)
        order_sql = self._build_order(sort_by, reverse)
        return self._wrapped.get_page_short(
            k, n, where_sql, where_params, order_sql
        )

    def get_count(
        self, filter_by=None, sort_by=None, reverse: bool = False
    ) -> int:
        if callable(filter_by):
            clients = self._filter_sort_in_memory(
                self.get_all(), filter_by, sort_by, reverse
            )
            return len(clients)

        where_sql, where_params = self._build_where(filter_by)
        return self._wrapped.get_filtered_count(where_sql, where_params)

    def _build_where(self, filter_by) -> tuple:
        if filter_by is None:
            return "", ()
        if not isinstance(filter_by, dict):
            raise TypeError(
                "filter_by для БД должен быть словарём условий "
                "или вызываемым объектом."
            )

        clauses = []
        params = []
        for field_name, expected in filter_by.items():
            if field_name not in self.COLUMN_MAP:
                raise ValueError(
                    f"Недопустимое поле фильтра: {field_name}. "
                    f"Допустимы: {', '.join(sorted(self.COLUMN_MAP))}."
                )
            column = self.COLUMN_MAP[field_name]
            clauses.append(f"{column} = %s")
            params.append(expected)

        if not clauses:
            return "", ()
        return "WHERE " + " AND ".join(clauses), tuple(params)

    def _build_order(self, sort_by, reverse: bool) -> str:
        if sort_by is None:
            return ""
        if callable(sort_by):
            raise TypeError(
                "sort_by для БД должен быть именем поля, а не функцией."
            )
        if not isinstance(sort_by, str):
            raise TypeError("sort_by должен быть именем поля или None.")
        if sort_by not in self.ALLOWED_SORT_FIELDS:
            raise ValueError(
                f"Недопустимое поле сортировки: {sort_by}. "
                f"Допустимы: {', '.join(sorted(self.ALLOWED_SORT_FIELDS))}."
            )
        column = self.COLUMN_MAP[sort_by]
        direction = "DESC" if reverse else "ASC"
        return f"ORDER BY {column} {direction}"