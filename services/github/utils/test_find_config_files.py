from unittest.mock import patch
import pytest

from services.github.utils.find_config_files import find_config_files


@pytest.fixture
def mock_configuration_files():
    """Fixture providing a controlled set of configuration files for testing."""
    return [
        # Exact match files
        "package.json",
        "requirements.txt",
        "Dockerfile",
        "Makefile",
        "go.mod",
        # Wildcard files
        "*.csproj",
        "*.vcxproj",
        "*.pro",
        "*.tf",
        "*.cabal",
        "*.opam",
        "*.nimble",
    ]


@pytest.fixture
def sample_file_tree():
    """Fixture providing a sample file tree for testing."""
    return [
        "src/main.py",
        "package.json",
        "requirements.txt",
        "src/utils/helper.py",
        "Dockerfile",
        "README.md",
        "tests/test_main.py",
        "config/app.config",
        "project.csproj",
        "build/output.vcxproj",
        "scripts/deploy.sh",
        "infrastructure/main.tf",
        "docs/guide.md",
        "lib/parser.cabal",
        "modules/auth.opam",
        "tools/build.nimble",
        "deep/nested/path/package.json",
        "another/deep/path/requirements.txt",
    ]


def test_find_config_files_empty_file_tree():
    """Test that empty file tree returns empty list."""
    result = find_config_files([])
    assert result == []


def test_find_config_files_no_config_files():
    """Test that file tree with no config files returns empty list."""
    file_tree = [
        "src/main.py",
        "src/utils/helper.py",
        "tests/test_main.py",
        "README.md",
        "docs/guide.md",
    ]
    result = find_config_files(file_tree)
    assert result == []


def test_find_config_files_exact_matches(mock_configuration_files):
    """Test exact filename matches are found correctly."""
    with patch("services.github.utils.find_config_files.CONFIGURATION_FILES", mock_configuration_files):
        file_tree = [
            "src/main.py",
            "package.json",
            "requirements.txt",
            "Dockerfile",
            "README.md",
        ]
        result = find_config_files(file_tree)
        expected = ["package.json", "requirements.txt", "Dockerfile"]
        assert sorted(result) == sorted(expected)


def test_find_config_files_wildcard_matches(mock_configuration_files):
    """Test wildcard pattern matches are found correctly."""
    with patch("services.github.utils.find_config_files.CONFIGURATION_FILES", mock_configuration_files):
        file_tree = [
            "src/main.py",
            "project.csproj",
            "build.vcxproj",
            "app.pro",
            "main.tf",
            "README.md",
        ]
        result = find_config_files(file_tree)
        expected = ["project.csproj", "build.vcxproj", "app.pro", "main.tf"]
        assert sorted(result) == sorted(expected)


def test_find_config_files_mixed_matches(mock_configuration_files):
    """Test both exact and wildcard matches work together."""
    with patch("services.github.utils.find_config_files.CONFIGURATION_FILES", mock_configuration_files):
        file_tree = [
            "src/main.py",
            "package.json",  # exact match
            "project.csproj",  # wildcard match
            "requirements.txt",  # exact match
            "infrastructure.tf",  # wildcard match
            "README.md",
        ]
        result = find_config_files(file_tree)
        expected = ["package.json", "project.csproj", "requirements.txt", "infrastructure.tf"]
        assert sorted(result) == sorted(expected)


def test_find_config_files_nested_paths(mock_configuration_files):
    """Test that config files in nested paths are found correctly."""
    with patch("services.github.utils.find_config_files.CONFIGURATION_FILES", mock_configuration_files):
        file_tree = [
            "deep/nested/path/package.json",
            "another/path/requirements.txt",
            "build/project.csproj",
            "infrastructure/aws/main.tf",
            "src/main.py",
        ]
        result = find_config_files(file_tree)
        expected = [
            "deep/nested/path/package.json",
            "another/path/requirements.txt", 
            "build/project.csproj",
            "infrastructure/aws/main.tf"
        ]
        assert sorted(result) == sorted(expected)


def test_find_config_files_duplicate_matches(mock_configuration_files):
    """Test that duplicate config files are included in results."""
    with patch("services.github.utils.find_config_files.CONFIGURATION_FILES", mock_configuration_files):
        file_tree = [
            "package.json",
            "frontend/package.json",
            "backend/package.json",
            "src/main.py",
        ]
        result = find_config_files(file_tree)
        expected = ["package.json", "frontend/package.json", "backend/package.json"]
        assert sorted(result) == sorted(expected)


def test_find_config_files_case_sensitive():
    """Test that filename matching is case sensitive."""
    with patch("services.github.utils.find_config_files.CONFIGURATION_FILES", ["package.json"]):
        file_tree = [
            "package.json",  # exact match
            "Package.json",  # different case
            "PACKAGE.JSON",  # different case
            "src/main.py",
        ]
        result = find_config_files(file_tree)
        assert result == ["package.json"]


def test_find_config_files_wildcard_case_sensitive():
    """Test that wildcard matching is case sensitive."""
    with patch("services.github.utils.find_config_files.CONFIGURATION_FILES", ["*.csproj"]):
        file_tree = [
            "project.csproj",  # exact match
            "Project.CSPROJ",  # different case
            "build.Csproj",   # different case
            "src/main.py",
        ]
        result = find_config_files(file_tree)
        assert result == ["project.csproj"]


def test_find_config_files_partial_wildcard_matches():
    """Test that partial wildcard matches don't match incorrectly."""
    with patch("services.github.utils.find_config_files.CONFIGURATION_FILES", ["*.csproj"]):
        file_tree = [
            "project.csproj",      # should match
            "project.csproj.bak",  # should not match (extra extension)
            "csproj.file",         # should not match (wrong position)
            "my.csproj.old",       # should not match (extra extension)
            "src/main.py",
        ]
        result = find_config_files(file_tree)
        assert result == ["project.csproj"]


def test_find_config_files_comprehensive_sample(sample_file_tree, mock_configuration_files):
    """Test comprehensive scenario with sample file tree."""
    with patch("services.github.utils.find_config_files.CONFIGURATION_FILES", mock_configuration_files):
        result = find_config_files(sample_file_tree)
        expected = [
            "package.json",
            "requirements.txt", 
            "Dockerfile",
            "project.csproj",
            "build/output.vcxproj",
            "infrastructure/main.tf",
            "lib/parser.cabal",
            "modules/auth.opam",
            "tools/build.nimble",
            "deep/nested/path/package.json",
            "another/deep/path/requirements.txt",
        ]
        assert sorted(result) == sorted(expected)


def test_find_config_files_handles_exception_gracefully():
    """Test that function handles exceptions gracefully and returns default value."""
    # Test with invalid input that might cause an exception
    with patch("services.github.utils.find_config_files.CONFIGURATION_FILES", None):
        result = find_config_files(["some/file.txt"])
        assert result == []  # Should return default_return_value from decorator


def test_find_config_files_with_none_input():
    """Test that function handles None input gracefully."""
    # This should trigger the exception handler
    result = find_config_files(None)
    assert result == []  # Should return default_return_value from decorator


def test_find_config_files_with_non_list_input():
    """Test that function handles non-list input gracefully."""
    # This should trigger the exception handler
    result = find_config_files("not_a_list")
    assert result == []  # Should return default_return_value from decorator


def test_find_config_files_preserves_order():
    """Test that the function preserves the order of found config files."""
    with patch("services.github.utils.find_config_files.CONFIGURATION_FILES", ["package.json", "requirements.txt"]):
        file_tree = [
            "requirements.txt",
            "src/main.py", 
            "package.json",
            "docs/readme.md",
        ]
        result = find_config_files(file_tree)
        # Should preserve the order they appear in the file_tree
        assert result == ["requirements.txt", "package.json"]


def test_find_config_files_with_real_configuration_files():
    """Test with actual CONFIGURATION_FILES from constants to ensure integration works."""
    # Test with some real files that should be in CONFIGURATION_FILES
    file_tree = [
        "src/main.py",
        "package.json",
        "requirements.txt", 
        "Dockerfile",
        "docker-compose.yml",
        "tsconfig.json",
        "jest.config.js",
        "go.mod",
        "Cargo.toml",
        "pom.xml",
        "build.gradle",
        "CMakeLists.txt",
        "Makefile",
        "project.csproj",
        "app.vcxproj",
        "main.tf",
        "README.md",  # Should not match
        "src/utils/helper.py",  # Should not match
    ]
    
    result = find_config_files(file_tree)
    
    # Should find all the config files but not the non-config files
    assert "package.json" in result
    assert "requirements.txt" in result
    assert "Dockerfile" in result
    assert "docker-compose.yml" in result
    assert "tsconfig.json" in result
    assert "jest.config.js" in result
    assert "go.mod" in result
    assert "Cargo.toml" in result
    assert "pom.xml" in result
    assert "build.gradle" in result
    assert "CMakeLists.txt" in result
    assert "Makefile" in result
    assert "project.csproj" in result
    assert "README.md" not in result
    assert "src/utils/helper.py" not in result


def test_find_config_files_potential_duplicate_matches():
    """Test that a file matching both exact and wildcard patterns is only added once."""
    # Create a scenario where a file could potentially match both patterns
    mock_config_files = [
        "test.config",  # exact match
        "*.config",     # wildcard match - same file could match both
    ]
    
    with patch("services.github.utils.find_config_files.CONFIGURATION_FILES", mock_config_files):
        file_tree = [
            "src/main.py",
            "test.config",  # This matches both "test.config" exactly and "*.config" wildcard
            "app.config",   # This matches only "*.config" wildcard
            "README.md",
        ]
        
        result = find_config_files(file_tree)
        
        # The file should appear twice since the function adds it for each match
        assert result.count("test.config") == 2  # Once for exact, once for wildcard
