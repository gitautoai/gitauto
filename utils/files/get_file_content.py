import os
from config import UTF8
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value="", raise_on_error=False)
def get_file_content(file_path: str):
    # Check if file exists before reading
    print(f"get_file_content - file exists: {os.path.exists(file_path)}")
    with open(file=file_path, mode="r", encoding=UTF8, newline="\n") as file:
        return file.read()
