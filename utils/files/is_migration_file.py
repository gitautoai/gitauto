def is_migration_file(file_path: str):

    file_path_lower = file_path.lower()

    migration_patterns = [
        "migration",
        "migrate",
        "/migrations/",
        "\\migrations\\",
        "alembic",
        "schema_migration",
        "db_migration",
        "database_migration",
    ]

    return any(pattern in file_path_lower for pattern in migration_patterns)
