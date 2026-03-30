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
    test_files = find_test_files(str(tmp_path), "services/github/client.py")
    assert "tests/services/github/test_client.py" in test_files


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
    test_files = find_test_files(str(tmp_path), "src/routes/middleware/audit-event.ts")
    assert "test/spec/routes/middleware/audit-event.spec.ts" in test_files


def test_finds_jest_test_file(tmp_path):
    _create_file(
        tmp_path, "src/components/Button.tsx", "export const Button = () => {}"
    )
    _create_file(
        tmp_path,
        "src/components/Button.test.tsx",
        "import { Button } from './Button'",
    )
    test_files = find_test_files(str(tmp_path), "src/components/Button.tsx")
    assert "src/components/Button.test.tsx" in test_files


def test_excludes_impl_file_itself(tmp_path):
    _create_file(tmp_path, "lib/utils.py", "def helper(): pass")
    test_files = find_test_files(str(tmp_path), "lib/utils.py")
    assert "lib/utils.py" not in test_files


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
    test_files = find_test_files(str(tmp_path), "services/client.py")
    assert "tests/test_client.py" in test_files
    assert "services/api.py" not in test_files


def test_returns_empty_for_missing_dir():
    test_files = find_test_files("/nonexistent/path", "foo.py")
    assert not test_files


def test_returns_empty_when_no_matches(tmp_path):
    _create_file(tmp_path, "src/main.py", "print('hello')")
    test_files = find_test_files(str(tmp_path), "src/other.py")
    assert not test_files


def test_finds_go_test_file(tmp_path):
    _create_file(tmp_path, "pkg/handler/handler.go", "package handler")
    _create_file(
        tmp_path,
        "pkg/handler/handler_test.go",
        "package handler\nimport handler",
    )
    test_files = find_test_files(str(tmp_path), "pkg/handler/handler.go")
    assert "pkg/handler/handler_test.go" in test_files


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
    test_files = find_test_files(
        str(tmp_path), "src/main/java/com/example/Service.java"
    )
    assert "src/test/java/com/example/ServiceTest.java" in test_files


def test_index_tsx_finds_test_via_content_grep(tmp_path):
    """index.tsx: Quote.test.tsx found via content grep because it references './index'."""
    _create_file(
        tmp_path,
        "src/pages/Quote/index.tsx",
        "export const QuotePage = () => {}",
    )
    _create_file(
        tmp_path,
        "src/pages/Quote/Quote.test.tsx",
        "import { QuotePage } from './index'",
    )
    _create_file(
        tmp_path,
        "tests/test_index_utils.py",
        "# This file mentions index but is unrelated",
    )
    test_files = find_test_files(str(tmp_path), "src/pages/Quote/index.tsx")
    # Found via content grep: Quote.test.tsx contains "./index"
    assert "src/pages/Quote/Quote.test.tsx" in test_files
    # Also found: test_index_utils.py contains "index" and has test_ prefix
    assert "tests/test_index_utils.py" in test_files


def test_colocated_test_found_without_stem_in_content(tmp_path):
    """Colocated test importing via './index' without mentioning parent dir name."""
    _create_file(
        tmp_path,
        "src/pages/Quote/index.tsx",
        "export default function Page() {}",
    )
    _create_file(
        tmp_path,
        "src/pages/Quote/index.test.tsx",
        "import Page from './index';\ntest('renders', () => {});",
    )
    test_files = find_test_files(str(tmp_path), "src/pages/Quote/index.tsx")
    assert "src/pages/Quote/index.test.tsx" in test_files


def test_finds_multiple_test_files(tmp_path):
    _create_file(tmp_path, "lib/core.py", "core_func = 1")
    for i in range(3):
        _create_file(
            tmp_path,
            f"tests/test_core_{i}.py",
            "from lib.core import core_func",
        )
    test_files = find_test_files(str(tmp_path), "lib/core.py")
    assert len(test_files) == 3


# ---- Real repo structure tests (Foxquilt foxcom-forms) ----


def test_foxquilt_index_tsx_finds_colocated_tests(tmp_path):
    """foxcom-forms: src/pages/Quote/index.tsx - stem is 'index', finds colocated test
    but not Quote.master.test.tsx (which doesn't reference 'index' in path or content).
    """
    _create_file(
        tmp_path,
        "src/pages/Quote/index.tsx",
        "import { Quote } from './Quote';\nexport default Quote;",
    )
    _create_file(
        tmp_path,
        "src/pages/Quote/Quote.tsx",
        "export const Quote = () => {};",
    )
    _create_file(
        tmp_path,
        "src/pages/Quote/index.test.tsx",
        "import Quote from './index';\ntest('renders', () => {});",
    )
    _create_file(
        tmp_path,
        "src/pages/Quote/Quote.master.test.tsx",
        "import { Quote } from './Quote';\ntest('Quote renders', () => {});",
    )
    test_files = find_test_files(str(tmp_path), "src/pages/Quote/index.tsx")
    assert "src/pages/Quote/index.test.tsx" in test_files
    # Quote.master.test.tsx doesn't contain "index" in path or content, so not found
    assert "src/pages/Quote/Quote.master.test.tsx" not in test_files


def test_foxquilt_auth_provider(tmp_path):
    """foxcom-forms: src/auth/AuthProvider.tsx with colocated and importing test files."""
    _create_file(
        tmp_path,
        "src/auth/AuthProvider.tsx",
        "export const AuthProvider = () => {};",
    )
    _create_file(
        tmp_path,
        "src/auth/AuthProvider.test.tsx",
        "import { AuthProvider } from './AuthProvider';\ntest('auth', () => {});",
    )
    # Test file that imports AuthProvider but doesn't have "AuthProvider" in its path
    _create_file(
        tmp_path,
        "src/pages/Quote/Quote.master.test.tsx",
        "import { AuthProvider } from '../../auth/AuthProvider';\ntest('quote', () => {});",
    )
    test_files = find_test_files(str(tmp_path), "src/auth/AuthProvider.tsx")
    assert "src/auth/AuthProvider.test.tsx" in test_files
    # Content grep should also find this test file referencing AuthProvider
    assert "src/pages/Quote/Quote.master.test.tsx" in test_files


# ---- Real repo structure tests (SPIDERPLUS-web) ----


def test_spiderplus_php_service(tmp_path):
    """SPIDERPLUS-web: core/app/Services/ -> core/tests/Unit/Service/ (separate dirs)."""
    _create_file(
        tmp_path,
        "core/app/Services/SafetypatService.php",
        "<?php\nclass SafetypatService { public function get() {} }",
    )
    _create_file(
        tmp_path,
        "core/tests/Unit/Service/SafetypatServiceTest.php",
        "<?php\nuse App\\Services\\SafetypatService;\nclass SafetypatServiceTest extends TestCase {}",
    )
    test_files = find_test_files(
        str(tmp_path), "core/app/Services/SafetypatService.php"
    )
    assert "core/tests/Unit/Service/SafetypatServiceTest.php" in test_files


def test_spiderplus_php_controller(tmp_path):
    """SPIDERPLUS-web: controller -> feature test in separate tests/ dir."""
    _create_file(
        tmp_path,
        "core/app/Http/Controllers/Api/V1/Safetypat/SafetypatController.php",
        "<?php\nclass SafetypatController { public function index() {} }",
    )
    _create_file(
        tmp_path,
        "core/tests/Feature/Api/V1/Safetypat/SafetypatControllerTest.php",
        "<?php\nclass SafetypatControllerTest extends TestCase { public function test_index() {} }",
    )
    test_files = find_test_files(
        str(tmp_path),
        "core/app/Http/Controllers/Api/V1/Safetypat/SafetypatController.php",
    )
    assert (
        "core/tests/Feature/Api/V1/Safetypat/SafetypatControllerTest.php" in test_files
    )


def test_spiderplus_js_loading_component(tmp_path):
    """SPIDERPLUS-web: JS component test in separate tests/ dir."""
    _create_file(
        tmp_path,
        "core/resources/assets/js/components/common/Loading.vue",
        "<template><div class='Loading'>Loading...</div></template>",
    )
    _create_file(
        tmp_path,
        "core/resources/tests/components/common/Loading.test.js",
        "import Loading from '../../assets/js/components/common/Loading.vue';\ntest('Loading', () => {});",
    )
    test_files = find_test_files(
        str(tmp_path), "core/resources/assets/js/components/common/Loading.vue"
    )
    assert "core/resources/tests/components/common/Loading.test.js" in test_files
