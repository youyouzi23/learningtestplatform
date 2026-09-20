from app import database


def test_database_configuration_exposes_valid_sqlalchemy_url() -> None:
    assert database.DATABASE_URL
    assert database.engine.url.drivername in {"sqlite", "mysql+pymysql"}
