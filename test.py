"""Проверки классов Client и репозиториев.

Запуск: python test.py
"""

import os

from client import Client, ClientMapper
from client_rep_adapter import Client_rep_DB_Adapter
from client_rep_db import Client_rep_DB
from client_rep_decorator import ClientRepositoryFilterSortDecorator
from client_rep_json import Client_rep_json
from client_rep_yaml import Client_rep_yaml
from repository_base import ClientRepositoryBase


def test_client_class():
    print("=== ТЕСТ КЛАССА CLIENT И ВАЛИДАЦИИ ===")

    client1 = Client(1, "Иванов", "Иван", "1111 222222", "9001112233")
    assert client1.client_id == 1
    assert client1.last_name == "Иванов"
    assert client1.phone_number == "9001112233"
    print(f"Успешно: {client1}")
    print(f"Краткая версия: {ClientMapper.short_version(client1)}")

    client2 = Client(
        '{"client_id": 2, "last_name": "Петров", "first_name": "Петр", '
        '"passport_data": "3333 444444", "phone_number": "9009998877"}'
    )
    assert client2.client_id == 2
    assert client2.last_name == "Петров"
    print(f"Из JSON: {client2}")

    client_from_dict = Client(
        {
            "client_id": 5,
            "last_name": "Орлов",
            "first_name": "Олег",
            "passport_data": "7777 888888",
            "phone_number": "9001110000",
        }
    )
    assert client_from_dict.last_name == "Орлов"
    print(f"Из словаря: {client_from_dict}")

    client3 = Client("3, Сидоров, Алексей, 1111 222222, 9005554433")
    assert client3.client_id == 3
    assert client3.last_name == "Сидоров"
    assert client3.first_name == "Алексей"
    print(f"Из CSV: {client3}")

    assert (client1 == client3) is True
    assert (client1 == client2) is False
    assert len({client1, client3}) == 1
    assert len({client1, client2}) == 2
    print("Сравнение и хэширование работают.")

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
    print("Валидация некорректных данных работает.\n")


def test_file_round_trip(repo_class, file_path: str):
    print(f"=== СОХРАНЕНИЕ/ЗАГРУЗКА: {repo_class.__name__} ===")
    if os.path.exists(file_path):
        os.remove(file_path)

    writer = repo_class(file_path)
    writer.add(Client(1, "Иванов", "Иван", "1234 567890", "9001112233"))
    writer.add(Client(1, "Петров", "Петр", "5555 666666", "9009998877"))
    writer.write_to_file()

    reader = repo_class(file_path)
    assert reader.get_count() == writer.get_count() == 2
    print(f"Round-trip OK: {reader.get_count()} клиентов.\n")


def test_repository(repo, persist=None):
    print(f"=== ТЕСТИРОВАНИЕ РЕПОЗИТОРИЯ: {repo.__class__.__name__} ===")

    start_count = repo.get_count()

    first = Client(1, "Смирнов", "Алексей", "1234 567890", "9990001122")
    second = Client(1, "Кузнецова", "Анна", "0987 654321", "9992223344")
    third = Client(1, "Васильев", "Василий", "5555 666666", "9994445566")
    repo.add(first)
    repo.add(second)
    repo.add(third)
    assert repo.get_count() == start_count + 3
    assert first.client_id and second.client_id and third.client_id
    print(f"Добавлено 3 клиента. Всего: {repo.get_count()}")

    found = repo.get_by_id(first.client_id)
    assert found == first
    print(f"Найден по ID {first.client_id}: {found}")

    updated = Client(
        first.client_id, "Смирнов-Обновленный", "Алексей", "1234 567890", "9990001122"
    )
    repo.update(first.client_id, updated)
    assert repo.get_by_id(first.client_id).last_name == "Смирнов-Обновленный"
    print(f"После обновления: {repo.get_by_id(first.client_id)}")

    short_list = repo.get_k_n_short_list(2, 1)
    assert len(short_list) == 2
    print("Страница (k=2, n=1):")
    for index, short_client in enumerate(short_list):
        print(f"  [{index + 1}] {short_client}")

    try:
        repo.get_k_n_short_list(0, 1)
    except ValueError:
        pass
    else:
        raise AssertionError("Ожидалось ValueError для k=0")

    repo.delete(second.client_id)
    assert repo.get_count() == start_count + 2
    try:
        repo.get_by_id(second.client_id)
    except ValueError:
        pass
    else:
        raise AssertionError("Удалённый клиент всё ещё доступен по ID")

    try:
        repo.delete(second.client_id)
    except ValueError:
        pass
    else:
        raise AssertionError("Повторное удаление должно вызывать ValueError")
    print(f"Удалён ID {second.client_id}. Всего: {repo.get_count()}")

    if persist is not None:
        persist()
        print("Данные сохранены на диск.")
    print()


def test_filter_sort_decorator(repo):
    print(f"=== ДЕКОРАТОР ФИЛЬТРА/СОРТИРОВКИ: {repo.__class__.__name__} ===")
    decorated = ClientRepositoryFilterSortDecorator(repo)

    total = decorated.get_count()
    assert total == repo.get_count()

    filtered_count = decorated.get_count(
        filter_by=lambda client: client.last_name.startswith("С")
    )
    print(f"Всего: {total}, с фамилией на 'С': {filtered_count}")

    page = decorated.get_k_n_short_list(2, 1, sort_by="last_name")
    assert len(page) <= 2
    print("Первая страница после сортировки по фамилии:")
    for short_client in page:
        print(f"  - {short_client}")

    second_page = decorated.get_k_n_short_list(1, 2, sort_by="last_name")
    assert len(second_page) <= 1
    print(f"Вторая страница (k=1, n=2): {second_page[0] if second_page else 'пусто'}")
    print()


if __name__ == "__main__":
    test_client_class()
    test_file_round_trip(Client_rep_json, "test_data.json")
    test_file_round_trip(Client_rep_yaml, "test_data.yaml")

    json_repo = Client_rep_json("test_data.json")
    assert isinstance(json_repo, ClientRepositoryBase)
    test_repository(json_repo, persist=json_repo.write_to_file)
    test_filter_sort_decorator(json_repo)

    yaml_repo = Client_rep_yaml("test_data.yaml")
    assert isinstance(yaml_repo, ClientRepositoryBase)
    test_repository(yaml_repo, persist=yaml_repo.write_to_file)
    test_filter_sort_decorator(yaml_repo)

    if not os.environ.get("DB_PASSWORD"):
        print(
            "ПРОПУСК ТЕСТА БД: не задана переменная окружения DB_PASSWORD.\n"
            "  Windows (PowerShell): $env:DB_PASSWORD='...'; python test.py\n"
            "  Linux/macOS:          DB_PASSWORD='...' python test.py\n"
        )
    else:
        db_config = {
            "dbname": os.environ.get("DB_NAME", "Lombard"),
            "user": os.environ.get("DB_USER", "postgres"),
            "password": os.environ["DB_PASSWORD"],
            "host": os.environ.get("DB_HOST", "localhost"),
        }
        db_repo = Client_rep_DB(db_config)
        adapter = Client_rep_DB_Adapter(db_repo)
        assert isinstance(adapter, ClientRepositoryBase)
        decorated_db = ClientRepositoryFilterSortDecorator(adapter)
        test_repository(decorated_db)
        test_filter_sort_decorator(adapter)

    print("ПРОВЕРКИ ДЛЯ ДОСТУПНЫХ РЕПОЗИТОРИЕВ ПРОЙДЕНЫ.")
