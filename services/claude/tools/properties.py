END_LINE: dict[str, str] = {
    "type": "integer",
    "description": "Ending line number for a specific range of lines to retrieve from the file. If start_line is not provided, will retrieve from beginning of file to end_line.",
}
FILE_PATH: dict[str, str] = {
    "type": "string",
    "description": "The full path to the file within the repository. For example, 'src/openai/__init__.py'. NEVER EVER be the same as the file_path in previous function calls.",
}
KEYWORD: dict[str, str] = {
    "type": "string",
    "description": "The keyword to search for in a file. For example, 'variable_name'. Exact matches only.",
}
LINE_NUMBER: dict[str, str] = {
    "type": "integer",
    "description": "If you already know the line number of interest when opening a file, use this. The 5 lines before and after this line number will be retrieved. For example, use it when checking the surrounding lines of a specific line number if the diff is incorrect. Cannot be used with start_line/end_line.",
}
START_LINE: dict[str, str] = {
    "type": "integer",
    "description": "Starting line number for a specific range of lines to retrieve from the file. If end_line is not provided, will retrieve from start_line to end of file.",
}
