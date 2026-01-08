from utils.files.is_migration_file import is_migration_file


def test_is_migration_file_with_migration_in_filename():
    assert is_migration_file("001_create_users_migration.py") is True
    assert is_migration_file("add_column_migration.sql") is True
    assert is_migration_file("user_migrate_v2.py") is True


def test_is_migration_file_with_migrations_directory():
    assert is_migration_file("db/migrations/001_create_tables.py") is True
    assert is_migration_file("app/migrations/add_users.sql") is True
    assert is_migration_file("src\\migrations\\schema_update.py") is True
    assert is_migration_file("php/migration/CreateTbRoomSnapshotDownTest.php") is True


def test_is_migration_file_with_alembic():
    assert is_migration_file("alembic/versions/001_initial.py") is True
    assert is_migration_file("migrations/alembic_env.py") is True


def test_is_migration_file_with_schema_patterns():
    assert is_migration_file("schema_migration_001.py") is True
    assert is_migration_file("db_migration_helper.py") is True
    assert is_migration_file("database_migration_runner.py") is True


def test_is_migration_file_with_regular_files():
    assert is_migration_file("user_model.py") is False
    assert is_migration_file("api_handler.py") is False
    assert is_migration_file("test_user.py") is False
    assert is_migration_file("config.py") is False


def test_is_migration_file_case_insensitive():
    assert is_migration_file("MIGRATION_001.PY") is True
    assert is_migration_file("Schema_Migration.sql") is True
    assert is_migration_file("DB/MIGRATIONS/init.py") is True


def test_is_migration_file_with_empty_string():
    assert is_migration_file("") is False
