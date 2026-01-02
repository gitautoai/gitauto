#!/usr/bin/env python3
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

db_password = os.getenv("SUPABASE_DB_PASSWORD_DEV")
if not db_password:
    print("Error: SUPABASE_DB_PASSWORD_DEV environment variable not set")
    sys.exit(1)

print("Generating TypedDict schemas from PostgreSQL...")

result = subprocess.run(
    [
        "psql",
        "-h",
        "aws-0-us-west-1.pooler.supabase.com",
        "-U",
        "postgres.dkrxtcbaqzrodvsagwwn",
        "-d",
        "postgres",
        "-p",
        "6543",
        "-t",
        "-c",
        """
        SELECT table_name, column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name NOT LIKE 'pg_%'
        ORDER BY table_name, ordinal_position;
        """,
    ],
    env={**os.environ, "PGPASSWORD": db_password},
    capture_output=True,
    text=True,
    check=False,
)

if result.returncode != 0:
    print(f"Error querying database: {result.stderr}")
    sys.exit(1)

tables = defaultdict(list)
for line in result.stdout.split("\n"):
    if line.strip():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) == 4:
            table_name, column_name, data_type, is_nullable = parts

            type_mapping = {
                "integer": "int",
                "bigint": "int",
                "text": "str",
                "character varying": "str",
                "boolean": "bool",
                "timestamp with time zone": "datetime.datetime",
                "timestamp without time zone": "datetime.datetime",
                "time without time zone": "datetime.time",
                "uuid": "str",
                "json": "dict[str, Any]",
                "jsonb": "dict[str, Any]",
                "real": "float",
                "double precision": "float",
                "numeric": "float",
            }

            PYTHON_TYPE = type_mapping.get(data_type, "Any")
            if is_nullable == "YES":
                PYTHON_TYPE = f"{PYTHON_TYPE} | None"

            tables[table_name].append(f"    {column_name}: {PYTHON_TYPE}")

output_path = Path(__file__).parent / "types.py"
with open(output_path, "w", encoding="utf-8") as f:
    f.write("import datetime\n")
    f.write("from typing import Any\n")
    f.write("from typing_extensions import TypedDict, NotRequired\n")
    f.write("\n\n")

    auto_fields = {"id", "created_at", "updated_at"}

    for table_name in sorted(tables.keys()):
        CLASS_NAME = "".join(word.capitalize() for word in table_name.split("_"))

        f.write(f"class {CLASS_NAME}(TypedDict):\n")
        if tables[table_name]:
            f.write("\n".join(tables[table_name]) + "\n")
        else:
            f.write("    pass\n")
        f.write("\n\n")

        insert_fields = []
        for field in tables[table_name]:
            field_name = field.strip().split(":")[0].strip()
            if field_name not in auto_fields:
                FIELD_TYPE = ":".join(field.strip().split(":")[1:]).strip()
                insert_fields.append(f"    {field_name}: NotRequired[{FIELD_TYPE}]")

        if insert_fields:
            f.write(f"class {CLASS_NAME}Insert(TypedDict):\n")
            f.write("\n".join(insert_fields) + "\n")
            if table_name != sorted(tables.keys())[-1]:
                f.write("\n\n")

print(f"Generated {len(tables) * 2} TypedDict classes (base + Insert) from PostgreSQL")
