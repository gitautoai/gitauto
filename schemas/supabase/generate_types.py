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
        SELECT table_name, column_name, data_type, is_nullable, udt_name
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
        if len(parts) == 5:
            table_name, column_name, data_type, is_nullable, udt_name = parts

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

            # PostgreSQL array udt_name starts with _ (e.g. _text, _int4, _bool)
            array_element_mapping = {
                "_text": "str",
                "_varchar": "str",
                "_int4": "int",
                "_int8": "int",
                "_bool": "bool",
                "_float4": "float",
                "_float8": "float",
                "_jsonb": "dict[str, Any]",
            }

            if data_type == "ARRAY":
                element_type = array_element_mapping.get(udt_name, "Any")
                PYTHON_TYPE = f"list[{element_type}]"
            else:
                PYTHON_TYPE = type_mapping.get(data_type, "Any")
            if is_nullable == "YES":
                PYTHON_TYPE = f"{PYTHON_TYPE} | None"

            tables[table_name].append(
                {
                    "name": column_name,
                    "type": PYTHON_TYPE,
                    "nullable": is_nullable == "YES",
                }
            )

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
            lines = [f"    {col['name']}: {col['type']}" for col in tables[table_name]]
            f.write("\n".join(lines) + "\n")
        else:
            f.write("    pass\n")
        f.write("\n\n")

        insert_fields = []
        for col in tables[table_name]:
            if col["name"] not in auto_fields:
                if col["nullable"]:
                    insert_fields.append(
                        f"    {col['name']}: NotRequired[{col['type']}]"
                    )
                else:
                    insert_fields.append(f"    {col['name']}: {col['type']}")

        if insert_fields:
            f.write(f"class {CLASS_NAME}Insert(TypedDict):\n")
            f.write("\n".join(insert_fields) + "\n")
            if table_name != sorted(tables.keys())[-1]:
                f.write("\n\n")

print(f"Generated {len(tables) * 2} TypedDict classes (base + Insert) from PostgreSQL")
