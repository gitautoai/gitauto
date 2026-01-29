from utils.files.guess_test_file_path import guess_test_file_path


def test_python_file():
    candidates = guess_test_file_path("services/github/client.py")
    assert candidates is not None
    assert "services/github/test_client.py" in candidates
    assert "services/github/client_test.py" in candidates
    assert "tests/services/github/test_client.py" in candidates
    assert "tests/services/github/client_test.py" in candidates


def test_typescript_file():
    candidates = guess_test_file_path("src/components/Button.tsx")
    assert candidates is not None
    assert "src/components/Button.test.tsx" in candidates
    assert "src/components/Button.spec.tsx" in candidates
    assert "__tests__/src/components/Button.test.tsx" in candidates
    assert "src/components/__tests__/Button.test.tsx" in candidates


def test_javascript_file():
    candidates = guess_test_file_path("lib/utils.js")
    assert candidates is not None
    assert "lib/utils.test.js" in candidates
    assert "lib/utils.spec.js" in candidates


def test_java_file():
    candidates = guess_test_file_path("com/example/Service.java")
    assert candidates is not None
    assert "com/example/ServiceTest.java" in candidates


def test_java_file_src_main():
    candidates = guess_test_file_path("src/main/java/com/example/Service.java")
    assert candidates is not None
    assert "src/main/java/com/example/ServiceTest.java" in candidates
    assert "src/test/java/com/example/ServiceTest.java" in candidates


def test_go_file():
    candidates = guess_test_file_path("pkg/handler/handler.go")
    assert candidates is not None
    assert "pkg/handler/handler_test.go" in candidates


def test_ruby_file():
    candidates = guess_test_file_path("lib/models/user.rb")
    assert candidates is not None
    assert "lib/models/user_spec.rb" in candidates
    assert "lib/models/user_test.rb" in candidates
    assert "spec/lib/models/user_spec.rb" in candidates
    assert "test/lib/models/user_test.rb" in candidates


def test_php_file():
    candidates = guess_test_file_path("app/Services/UserService.php")
    assert candidates is not None
    assert "app/Services/UserServiceTest.php" in candidates
    assert "tests/app/Services/UserServiceTest.php" in candidates


def test_rust_file():
    candidates = guess_test_file_path("src/lib.rs")
    assert candidates is not None
    assert "src/lib.rs" in candidates


def test_csharp_file():
    candidates = guess_test_file_path("Services/UserService.cs")
    assert candidates is not None
    assert "Services/UserServiceTests.cs" in candidates
    assert "Services/UserServiceTest.cs" in candidates


def test_kotlin_file():
    candidates = guess_test_file_path("com/example/Repository.kt")
    assert candidates is not None
    assert "com/example/RepositoryTest.kt" in candidates


def test_unsupported_extension():
    candidates = guess_test_file_path("README.md")
    assert candidates is None
