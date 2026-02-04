from utils.error.handle_exceptions import handle_exceptions

JS_TS_FILE_EXTENSIONS = (".js", ".jsx", ".ts", ".tsx")


@handle_exceptions(default_return_value=[], raise_on_error=False)
def filter_js_ts_files(file_paths: list[str]) -> list[str]:
    return [f for f in file_paths if f.endswith(JS_TS_FILE_EXTENSIONS)]
