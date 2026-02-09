from services.claude.sanitize_tool_args import sanitize_tool_args


def test_strips_antml_closing_tag():
    args: dict[str, object] = {"dir_path": "</antml :parameter>\n"}
    sanitize_tool_args(args)
    assert args["dir_path"] == ""


def test_strips_antml_after_valid_content():
    args: dict[str, object] = {"dir_path": "some/path</antml :parameter>\n"}
    sanitize_tool_args(args)
    assert args["dir_path"] == "some/path"


def test_leaves_clean_args_unchanged():
    args: dict[str, object] = {"dir_path": "tests/js/unit", "query": "hello"}
    sanitize_tool_args(args)
    assert args["dir_path"] == "tests/js/unit"
    assert args["query"] == "hello"


def test_leaves_non_string_values_unchanged():
    args: dict[str, object] = {"start_line": 1, "end_line": 50}
    sanitize_tool_args(args)
    assert args["start_line"] == 1
    assert args["end_line"] == 50


def test_strips_multiple_affected_keys():
    args: dict[str, object] = {
        "dir_path": "src</antml :parameter>",
        "query": "test</antml>",
    }
    sanitize_tool_args(args)
    assert args["dir_path"] == "src"
    assert args["query"] == "test"
