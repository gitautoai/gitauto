from utils.files.filter_js_ts_files import filter_js_ts_files


def test_filters_js_files():
    files = ["app.js", "index.jsx", "readme.md"]
    result = filter_js_ts_files(files)
    assert result == ["app.js", "index.jsx"]


def test_filters_ts_files():
    files = ["app.ts", "index.tsx", "config.json"]
    result = filter_js_ts_files(files)
    assert result == ["app.ts", "index.tsx"]


def test_filters_mixed_files():
    files = ["app.js", "index.ts", "style.css", "component.tsx", "utils.jsx"]
    result = filter_js_ts_files(files)
    assert result == ["app.js", "index.ts", "component.tsx", "utils.jsx"]


def test_empty_list():
    result = filter_js_ts_files([])
    assert result == []


def test_no_js_ts_files():
    files = ["readme.md", "config.json", "style.css"]
    result = filter_js_ts_files(files)
    assert result == []


def test_all_js_ts_files():
    files = ["app.js", "index.ts", "component.tsx", "utils.jsx"]
    result = filter_js_ts_files(files)
    assert result == ["app.js", "index.ts", "component.tsx", "utils.jsx"]
