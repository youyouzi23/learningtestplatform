import os
import time
import uuid

import pytest
from redis import Redis
from sqlalchemy import create_engine, text

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_INTEGRATION_TESTS") != "1",
        reason="set RUN_INTEGRATION_TESTS=1 with MySQL and Redis available",
    ),
]


def test_mysql_round_trip() -> None:
    database_url = os.environ["INTEGRATION_DATABASE_URL"]
    engine = create_engine(database_url)
    table_name = f"integration_probe_{uuid.uuid4().hex}"

    with engine.begin() as connection:
        connection.execute(
            text(f"CREATE TABLE {table_name} (id INT PRIMARY KEY, value VARCHAR(50))")
        )
        connection.execute(
            text(f"INSERT INTO {table_name} (id, value) VALUES (1, 'persisted')")
        )
        value = connection.execute(
            text(f"SELECT value FROM {table_name} WHERE id = 1")
        ).scalar_one()
        connection.execute(text(f"DROP TABLE {table_name}"))

    assert value == "persisted"
    engine.dispose()


def test_redis_ttl_and_delete() -> None:
    client = Redis.from_url(os.environ["INTEGRATION_REDIS_URL"], decode_responses=True)
    key = f"integration:{uuid.uuid4().hex}"

    client.setex(key, 2, "cached")
    assert client.get(key) == "cached"
    assert 0 < client.ttl(key) <= 2

    time.sleep(2.1)
    assert client.get(key) is None

    client.set(key, "delete-me")
    assert client.delete(key) == 1
    assert client.get(key) is None
