import os

from utils.files.find_test_files import find_test_files


def _create_file(base: str, rel_path: str, content: str = ""):
    full = os.path.join(base, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


def test_finds_python_test_file(tmp_path):
    _create_file(tmp_path, "services/github/client.py", "class GitHubClient: pass")
    _create_file(
        tmp_path,
        "tests/services/github/test_client.py",
        "from services.github.client import GitHubClient",
    )
    result = find_test_files(str(tmp_path), "services/github/client.py")
    assert "tests/services/github/test_client.py" in result


def test_finds_typescript_spec_file(tmp_path):
    _create_file(
        tmp_path,
        "src/routes/middleware/audit-event.ts",
        "export function auditEvent() {}",
    )
    _create_file(
        tmp_path,
        "test/spec/routes/middleware/audit-event.spec.ts",
        "import { auditEvent } from '../../routes/middleware/audit-event'",
    )
    result = find_test_files(str(tmp_path), "src/routes/middleware/audit-event.ts")
    assert "test/spec/routes/middleware/audit-event.spec.ts" in result


def test_finds_jest_test_file(tmp_path):
    _create_file(
        tmp_path, "src/components/Button.tsx", "export const Button = () => {}"
    )
    _create_file(
        tmp_path,
        "src/components/Button.test.tsx",
        "import { Button } from './Button'",
    )
    result = find_test_files(str(tmp_path), "src/components/Button.tsx")
    assert "src/components/Button.test.tsx" in result


def test_excludes_impl_file_itself(tmp_path):
    _create_file(tmp_path, "lib/utils.py", "def helper(): pass")
    # The impl file itself contains its own stem but should be excluded
    result = find_test_files(str(tmp_path), "lib/utils.py")
    assert "lib/utils.py" not in result


def test_excludes_non_test_files(tmp_path):
    _create_file(tmp_path, "services/client.py", "class Client: pass")
    _create_file(
        tmp_path,
        "services/api.py",
        "from services.client import Client",
    )
    _create_file(
        tmp_path,
        "tests/test_client.py",
        "from services.client import Client",
    )
    result = find_test_files(str(tmp_path), "services/client.py")
    assert "tests/test_client.py" in result
    assert "services/api.py" not in result


def test_returns_empty_for_missing_dir():
    result = find_test_files("/nonexistent/path", "foo.py")
    assert result == []


def test_returns_empty_when_no_matches(tmp_path):
    _create_file(tmp_path, "src/main.py", "print('hello')")
    result = find_test_files(str(tmp_path), "src/other.py")
    assert result == []


def test_finds_go_test_file(tmp_path):
    _create_file(tmp_path, "pkg/handler/handler.go", "package handler")
    _create_file(
        tmp_path,
        "pkg/handler/handler_test.go",
        "package handler\nimport handler",
    )
    result = find_test_files(str(tmp_path), "pkg/handler/handler.go")
    assert "pkg/handler/handler_test.go" in result


def test_finds_java_test_file(tmp_path):
    _create_file(
        tmp_path,
        "src/main/java/com/example/Service.java",
        "public class Service {}",
    )
    _create_file(
        tmp_path,
        "src/test/java/com/example/ServiceTest.java",
        "import com.example.Service;",
    )
    result = find_test_files(str(tmp_path), "src/main/java/com/example/Service.java")
    assert "src/test/java/com/example/ServiceTest.java" in result


def test_finds_multiple_test_files(tmp_path):
    _create_file(tmp_path, "lib/core.py", "core_func = 1")
    for i in range(3):
        _create_file(
            tmp_path,
            f"tests/test_core_{i}.py",
            "from lib.core import core_func",
        )
    result = find_test_files(str(tmp_path), "lib/core.py")
    assert len(result) == 3
