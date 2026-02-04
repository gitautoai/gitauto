from constants.files import JS_TS_FILE_EXTENSIONS
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def filter_js_ts_files(file_paths: list[str]) -> list[str]:
    return [f for f in file_paths if f.endswith(JS_TS_FILE_EXTENSIONS)]
