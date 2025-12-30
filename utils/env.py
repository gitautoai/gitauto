import os
from dotenv import load_dotenv

load_dotenv()


def get_env_var(name: str) -> str:
    value: str | None = os.environ.get(name)
    if value is None:
        raise ValueError(f"Environment variable {name} not set.")
    return value
