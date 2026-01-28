def is_migration_file(file_path: str):

    file_path_lower = file_path.lower()

    # Check if filename starts with "migration" (e.g., MIGRATION_001.PY)
    # Get basename (after last / or \)
    basename = file_path_lower.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    if basename.startswith("migration"):
        return True

    # Match migration patterns (avoid utility files like is_migration_file.py by using
    # underscore prefixes and directory patterns)
    migration_patterns = [
        # Directory patterns
        "/migrations/",
        "\\migrations\\",
        "migrations/",
        "/migration/",
        "\\migration\\",
        "migration/",
        "alembic/",
        "migrate-",
        # Filename patterns (won't match is_migration_file.py)
        "_migration.",
        "_migrate.",
        "_migrate_",
        # Schema patterns
        "schema_migration",
        "db_migration",
        "database_migration",
    ]

    return any(pattern in file_path_lower for pattern in migration_patterns)
