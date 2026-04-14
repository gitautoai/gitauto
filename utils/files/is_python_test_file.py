import os

from constants.files import PYTHON_TEST_FILE_PREFIX


def is_python_test_file(file_path: str):
    basename = os.path.basename(file_path)
    return basename.startswith(PYTHON_TEST_FILE_PREFIX) and file_path.endswith(".py")
