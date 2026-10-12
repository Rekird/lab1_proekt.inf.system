"""Проверки классов Client и репозиториев.

Запуск: python test.py
"""

import os

from client import Client, ClientMapper
from client_rep_adapter import Client_rep_DB_Adapter
from client_rep_db import Client_rep_DB
from client_rep_decorator import (
    ClientRepositoryDBSortFilterDecorator,
    ClientRepositoryFilterSortDecorator,
)
from client_rep_json import Client_rep_json
from client_rep_yaml import Client_rep_yaml
from repository_base import ClientRepositoryBase


def test_client():
    print("=== Класс Client и валидация ===")

    c1 = Client(1, "Иванов", "Иван", "1111 222222", "9001112233")
    c2 = Client(
        '{"client_id": 2, "last_name": "Петров", "first_name": "Петр", '
        '"passport_data": "3333 444444", "phone_number": "9009998877"}'
    )
    c3 = Client("3, Сидоров, Алексей, 1111 222222, 9005554433")
    c4 = Client(
        {
            "client_id": 5,
            "last_name": "Орлов",
            "first_name": "Олег",
            "passport_data": "7777 888888",
            "phone_number": "9001110000",
        }
    )

    print(f"  5 аргументов:        {c1}")
    print(f"  из JSON-строки:      {c2}")
    print(f"  из CSV-строки:       {c3}")
    print(f"  из словаря:          {c4}")
    print(f"  краткая версия:      {ClientMapper.short_version(c1)}")

    assert c1.client_id == 1 and c1.last_name == "Иванов"
    assert c2.last_name == "Петров"
    assert c3.first_name == "Алексей"
    assert c4.last_name == "Орлов"
    assert str(ClientMapper.short_version(c1)) == "Иванов И., Тел: 9001112233"

    assert c1 == c3            # равны по паспорту
    assert c1 != c2
    assert len({c1, c3}) == 1
    assert len({c1, c2}) == 2
    print("  сравнение и хэширование: ok")

    incorrect = (
        lambda: Client(0, "Иванов", "Иван", "1111 222222", "9001112233"),
        lambda: Client(True, "Иванов", "Иван", "1111 222222", "9001112233"),
        lambda: Client(1, "", "Иван", "1111 222222", "9001112233"),
        lambda: Client(1, "Иванов", "Иван", "12345", "9001112233"),
        lambda: Client(1, "Иванов", "Иван", "1111 222222", "abc"),
        lambda: Client("1, Иванов, Иван, только, четыре"),
    )
    for call in incorrect:
        try:
            call()
        except ValueError:
            pass
        else:
            raise AssertionError("Ожидалось ValueError для некорректных данных")
    print("  валидация некорректных данных: ok\n")


def test_file_round_trip(repo_class, path):
    print(f"=== Round-trip: {repo_class.__name__} ===")
    if os.path.exists(path):
        os.remove(path)

    writer = repo_class(path)
    writer.add(Client(1, "Иванов", "Иван", "1234 567890", "9001112233"))
    writer.add(Client(1, "Петров", "Петр", "5555 666666", "9009998877"))
    writer.write_to_file()

    reader = repo_class(path)
    assert reader.get_count() == writer.get_count() == 2
    print(f"  загружено клиентов: {reader.get_count()}\n")


def test_repository(repo, persist=None):
    print(f"=== Репозиторий: {repo.__class__.__name__} ===")
    start = repo.get_count()

    first = Client(1, "Смирнов", "Алексей", "1234 567890", "9990001122")
    second = Client(1, "Кузнецова", "Анна", "0987 654321", "9992223344")
    third = Client(1, "Васильев", "Василий", "5555 666666", "9994445566")
    repo.add(first)
    repo.add(second)
    repo.add(third)
    assert repo.get_count() == start + 3
    assert first.client_id and second.client_id and third.client_id
    print(f"  добавлено 3, всего: {repo.get_count()}")

    found = repo.get_by_id(first.client_id)
    assert found == first
    print(f"  поиск по ID {first.client_id}: {found}")

    updated = Client(
        first.client_id,
        "Смирнов-Обновленный",
        "Алексей",
        "1234 567890",
        "9990001122",
    )
    repo.update(first.client_id, updated)
    assert repo.get_by_id(first.client_id).last_name == "Смирнов-Обновленный"
    print(f"  после обновления:    {repo.get_by_id(first.client_id)}")

    page = repo.get_k_n_short_list(2, 1)
    assert len(page) == 2
    print("  страница k=2, n=1:")
    for i, sc in enumerate(page):
        print(f"    [{i + 1}] {sc}")

    try:
        repo.get_k_n_short_list(0, 1)
    except ValueError:
        print("  k=0: ValueError (ожидаемо)")
    else:
        raise AssertionError("k=0 должен падать")

    repo.delete(second.client_id)
    assert repo.get_count() == start + 2
    try:
        repo.get_by_id(second.client_id)
    except ValueError:
        print(f"  ID {second.client_id} удалён")
    else:
        raise AssertionError("Удалённый доступен по ID")

    try:
        repo.delete(second.client_id)
    except ValueError:
        pass
    else:
        raise AssertionError("Повторное удаление должно падать")

    if persist:
        persist()
        print("  данные сохранены на диск")
    print()


def test_file_decorator(repo):
    print(f"=== Файловый декоратор: {repo.__class__.__name__} ===")
    d = ClientRepositoryFilterSortDecorator(repo)
    assert d.get_count() == repo.get_count()

    total = d.get_count()
    filtered = d.get_count(filter_by=lambda c: c.last_name.startswith("С"))
    print(f"  всего: {total}, с фамилией на 'С': {filtered}")

    page = d.get_k_n_short_list(2, 1, sort_by="last_name")
    assert len(page) <= 2
    print("  первая страница (sort_by=last_name):")
    for sc in page:
        print(f"    - {sc}")

    second = d.get_k_n_short_list(1, 2, sort_by="last_name")
    assert len(second) <= 1
    tail = second[0] if second else "пусто"
    print(f"  вторая страница (k=1, n=2): {tail}")

    try:
        d.get_count(sort_by="unknown")
    except ValueError:
        print("  sort_by='unknown': ValueError (ожидаемо)")
    else:
        raise AssertionError("Ожидалось ValueError")
    print()


def test_db_decorator(adapter):
    print("=== SQL-декоратор для БД ===")
    d = ClientRepositoryDBSortFilterDecorator(adapter)
    print(f"  всего в БД: {d.get_count()}")

    page = d.get_k_n_short_list(2, 1, sort_by="last_name")
    assert len(page) <= 2
    print("  первая страница (ORDER BY last_name ASC):")
    for sc in page:
        print(f"    - {sc}")

    filtered = d.get_k_n_short_list(
        5, 1, filter_by={"last_name": "Иванов"}, sort_by="client_id"
    )
    print(f"  WHERE last_name='Иванов': {len(filtered)} записей")

    try:
        d.get_k_n_short_list(2, 1, filter_by={"unknown": "x"})
    except ValueError:
        print("  неизвестное поле фильтра: ValueError (ожидаемо)")
    else:
        raise AssertionError("Ожидалось ValueError для фильтра")

    try:
        d.get_k_n_short_list(2, 1, sort_by="unknown")
    except ValueError:
        print("  неизвестное поле сортировки: ValueError (ожидаемо)")
    else:
        raise AssertionError("Ожидалось ValueError для сортировки")
    print()


if __name__ == "__main__":
    test_client()
    test_file_round_trip(Client_rep_json, "test_data.json")
    test_file_round_trip(Client_rep_yaml, "test_data.yaml")

    json_repo = Client_rep_json("test_data.json")
    assert isinstance(json_repo, ClientRepositoryBase)
    test_repository(json_repo, persist=json_repo.write_to_file)
    test_file_decorator(json_repo)

    yaml_repo = Client_rep_yaml("test_data.yaml")
    assert isinstance(yaml_repo, ClientRepositoryBase)
    test_repository(yaml_repo, persist=yaml_repo.write_to_file)
    test_file_decorator(yaml_repo)

    if not os.environ.get("DB_PASSWORD"):
        print("ПРОПУСК БД: не задана переменная окружения DB_PASSWORD.")
    else:
        db_repo = Client_rep_DB(
            {
                "dbname": os.environ.get("DB_NAME", "Lombard"),
                "user": os.environ.get("DB_USER", "postgres"),
                "password": os.environ["DB_PASSWORD"],
                "host": os.environ.get("DB_HOST", "localhost"),
            }
        )
        adapter = Client_rep_DB_Adapter(db_repo)
        assert isinstance(adapter, ClientRepositoryBase)

        # Изоляция БД-тестов: чистим таблицу перед прогоном.
        with adapter.adaptee.db_manager.get_connection().cursor() as cur:
            cur.execute("TRUNCATE TABLE clients RESTART IDENTITY;")

        test_repository(ClientRepositoryFilterSortDecorator(adapter))
        test_db_decorator(adapter)

    print("ПРОВЕРКИ ДЛЯ ДОСТУПНЫХ РЕПОЗИТОРИЕВ ПРОЙДЕНЫ.")