from app.config import normalize_database_url, DevelopmentConfig, TestingConfig


def test_postgres_url_normalization():
    assert normalize_database_url("postgres://user:pass@host/db") == "postgresql://user:pass@host/db"
    assert normalize_database_url("postgresql://user:pass@host/db") == "postgresql://user:pass@host/db"
    assert normalize_database_url(None) == "postgresql://unconfigured_user:unconfigured_pass@localhost:5432/unconfigured_db"
    assert normalize_database_url("") == "postgresql://unconfigured_user:unconfigured_pass@localhost:5432/unconfigured_db"


def test_development_config():
    config = DevelopmentConfig()
    assert config.DEBUG is True
    assert config.TESTING is False


def test_testing_config(app):
    assert app.config["TESTING"] is True
    assert app.config["DEBUG"] is True
