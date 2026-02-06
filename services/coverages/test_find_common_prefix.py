from config import UTF8
from services.coverages.find_common_prefix import find_common_prefix


def test_strips_to_match():
    """Strips prefix to match known repo files."""
    lcov = """SF:/home/kf/app/php/class/security/function.php
DA:13,43
LF:1
LH:1
end_of_record
SF:/home/kf/app/php/web/index.php
DA:1,10
LF:1
LH:1
end_of_record"""
    repo_files = {"php/class/security/function.php", "php/web/index.php"}
    assert find_common_prefix(lcov, repo_files) == "/home/kf/app/"


def test_github_actions_runner():
    """GitHub Actions runner absolute paths are detected."""
    lcov = """SF:/home/runner/work/salidas/salidas/Salida/Core/Constantes.cs
DA:1,0
LF:1
LH:0
end_of_record
SF:/home/runner/work/salidas/salidas/Salida/Conversores.cs
DA:1,0
LF:1
LH:0
end_of_record"""
    repo_files = {"Salida/Core/Constantes.cs", "Salida/Conversores.cs"}
    assert find_common_prefix(lcov, repo_files) == "/home/runner/work/salidas/salidas/"


def test_no_match():
    """When no SF path matches repo_files, returns empty string."""
    lcov = """SF:/home/kf/app/php/file.php
DA:1,1
LF:1
LH:1
end_of_record"""
    repo_files = {"src/other.py"}
    assert find_common_prefix(lcov, repo_files) == ""


def test_relative_paths():
    """Relative paths in lcov return empty string."""
    lcov = """SF:src/main.py
DA:1,1
LF:1
LH:1
end_of_record"""
    repo_files = {"src/main.py"}
    assert find_common_prefix(lcov, repo_files) == ""


def test_empty_repo_files():
    """Empty repo_files returns empty string."""
    lcov = """SF:/home/kf/app/php/file.php
DA:1,1
LF:1
LH:1
end_of_record"""
    assert find_common_prefix(lcov, set()) == ""


def test_real_spiderplus_lcov():
    """Real SpiderPlus lcov matched against a known repo file."""
    with open("payloads/lcov/lcov-php-spiderplus.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()
    repo_files = {"php/class/security/function.php"}
    assert find_common_prefix(lcov_content, repo_files) == "/home/kf/app/"


def test_real_dotnet_lcov():
    """Real .NET lcov matched against a known repo file."""
    with open("payloads/lcov/lcov-dotnet-real.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()
    repo_files = {"Salida/Core/Constantes.cs"}
    assert (
        find_common_prefix(lcov_content, repo_files)
        == "/home/runner/work/salidas/salidas/"
    )


def test_real_python_lcov():
    """Real Python lcov has relative paths, no prefix to strip."""
    with open("payloads/lcov/lcov-python-sample.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()
    assert find_common_prefix(lcov_content, {"config.py"}) == ""


def test_real_javascript_lcov():
    """Real JavaScript lcov has relative paths, no prefix to strip."""
    with open("payloads/lcov/lcov-javascript-sample.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()
    assert find_common_prefix(lcov_content, {"app/global-error.jsx"}) == ""


def test_real_foxquilt_lcov():
    """Real Foxquilt (CircleCI) lcov has relative paths, no prefix to strip."""
    with open("payloads/lcov/lcov-js-foxquilt.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()
    assert find_common_prefix(lcov_content, {"src/App.tsx"}) == ""
