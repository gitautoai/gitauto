"""Tests for constants/dependency_files.py module."""

import pytest
from constants import dependency_files


class TestConfigurationFilesCss:
    """Test CONFIGURATION_FILES_CSS constant."""

    def test_configuration_files_css_is_list(self):
        """Test that CONFIGURATION_FILES_CSS is a list."""
        assert isinstance(dependency_files.CONFIGURATION_FILES_CSS, list)

    def test_configuration_files_css_not_empty(self):
        """Test that CONFIGURATION_FILES_CSS is not empty."""
        assert len(dependency_files.CONFIGURATION_FILES_CSS) > 0

    def test_configuration_files_css_contains_expected_files(self):
        """Test that CONFIGURATION_FILES_CSS contains expected CSS configuration files."""
        expected_files = [
            "tailwind.config.js",
            "tailwind.config.ts",
            "postcss.config.js",
            "postcss.config.ts",
            "styles/globals.css",
            "styles/styles.css",
            "styles/tailwind.ts",
        ]
        assert dependency_files.CONFIGURATION_FILES_CSS == expected_files


class TestConfigurationFilesNext:
    """Test CONFIGURATION_FILES_NEXT constant."""

    def test_configuration_files_next_is_list(self):
        """Test that CONFIGURATION_FILES_NEXT is a list."""
        assert isinstance(dependency_files.CONFIGURATION_FILES_NEXT, list)

    def test_configuration_files_next_contains_expected_files(self):
        """Test that CONFIGURATION_FILES_NEXT contains expected Next.js configuration files."""
        expected_files = [
            "next.config.js",
            "next.config.ts",
            "next.config.mjs",
            "next.config.mts",
            "next.config.cjs",
        ]
        assert dependency_files.CONFIGURATION_FILES_NEXT == expected_files


class TestConfigurationFilesJs:
    """Test CONFIGURATION_FILES_JS constant."""

    def test_configuration_files_js_is_list(self):
        """Test that CONFIGURATION_FILES_JS is a list."""
        assert isinstance(dependency_files.CONFIGURATION_FILES_JS, list)

    def test_configuration_files_js_contains_package_json(self):
        """Test that CONFIGURATION_FILES_JS contains package.json."""
        assert "package.json" in dependency_files.CONFIGURATION_FILES_JS

    def test_configuration_files_js_contains_jest_configs(self):
        """Test that CONFIGURATION_FILES_JS contains Jest configuration files."""
        jest_files = ["jest.config.js", "jest.config.ts", "jest.setup.js", "jest.setup.ts"]
        for jest_file in jest_files:
            assert jest_file in dependency_files.CONFIGURATION_FILES_JS


class TestConfigurationFilesPython:
    """Test CONFIGURATION_FILES_PYTHON constant."""

    def test_configuration_files_python_is_list(self):
        """Test that CONFIGURATION_FILES_PYTHON is a list."""
        assert isinstance(dependency_files.CONFIGURATION_FILES_PYTHON, list)

    def test_configuration_files_python_contains_requirements_txt(self):
        """Test that CONFIGURATION_FILES_PYTHON contains requirements.txt."""
        assert "requirements.txt" in dependency_files.CONFIGURATION_FILES_PYTHON

    def test_configuration_files_python_contains_dependency_managers(self):
        """Test that CONFIGURATION_FILES_PYTHON contains various dependency manager files."""
        dependency_files_list = ["requirements.txt", "Pipfile", "pyproject.toml", "conda.yaml", "environment.yml"]
        for dep_file in dependency_files_list:
            assert dep_file in dependency_files.CONFIGURATION_FILES_PYTHON


class TestConfigurationFilesRuby:
    """Test CONFIGURATION_FILES_RUBY constant."""

    def test_configuration_files_ruby_is_list(self):
        """Test that CONFIGURATION_FILES_RUBY is a list."""
        assert isinstance(dependency_files.CONFIGURATION_FILES_RUBY, list)

    def test_configuration_files_ruby_contains_gemfile(self):
        """Test that CONFIGURATION_FILES_RUBY contains Gemfile."""
        assert "Gemfile" in dependency_files.CONFIGURATION_FILES_RUBY


class TestConfigurationFilesPhp:
    """Test CONFIGURATION_FILES_PHP constant."""

    def test_configuration_files_php_is_list(self):
        """Test that CONFIGURATION_FILES_PHP is a list."""
        assert isinstance(dependency_files.CONFIGURATION_FILES_PHP, list)

    def test_configuration_files_php_contains_composer_json(self):
        """Test that CONFIGURATION_FILES_PHP contains composer.json."""
        assert "composer.json" in dependency_files.CONFIGURATION_FILES_PHP


class TestConfigurationFilesJava:
    """Test CONFIGURATION_FILES_JAVA constant."""

    def test_configuration_files_java_is_list(self):
        """Test that CONFIGURATION_FILES_JAVA is a list."""
        assert isinstance(dependency_files.CONFIGURATION_FILES_JAVA, list)

    def test_configuration_files_java_contains_maven_gradle(self):
        """Test that CONFIGURATION_FILES_JAVA contains Maven and Gradle files."""
        build_files = ["pom.xml", "build.gradle", "build.gradle.kts"]
        for build_file in build_files:
            assert build_file in dependency_files.CONFIGURATION_FILES_JAVA


class TestConfigurationFilesC:
    """Test CONFIGURATION_FILES_C constant."""

    def test_configuration_files_c_is_list(self):
        """Test that CONFIGURATION_FILES_C is a list."""
        assert isinstance(dependency_files.CONFIGURATION_FILES_C, list)

    def test_configuration_files_c_contains_cmake(self):
        """Test that CONFIGURATION_FILES_C contains CMakeLists.txt."""
        assert "CMakeLists.txt" in dependency_files.CONFIGURATION_FILES_C


class TestConfigurationFilesDotnet:
    """Test CONFIGURATION_FILES_DOTNET constant."""

    def test_configuration_files_dotnet_is_list(self):
        """Test that CONFIGURATION_FILES_DOTNET is a list."""
        assert isinstance(dependency_files.CONFIGURATION_FILES_DOTNET, list)

    def test_configuration_files_dotnet_contains_project_files(self):
        """Test that CONFIGURATION_FILES_DOTNET contains .NET project files."""
        project_files = ["*.csproj", "*.fsproj", "*.vbproj"]
        for project_file in project_files:
            assert project_file in dependency_files.CONFIGURATION_FILES_DOTNET


class TestConfigurationFilesGo:
    """Test CONFIGURATION_FILES_GO constant."""

    def test_configuration_files_go_is_list(self):
        """Test that CONFIGURATION_FILES_GO is a list."""
        assert isinstance(dependency_files.CONFIGURATION_FILES_GO, list)

    def test_configuration_files_go_contains_go_mod(self):
        """Test that CONFIGURATION_FILES_GO contains go.mod and go.sum."""
        assert "go.mod" in dependency_files.CONFIGURATION_FILES_GO
        assert "go.sum" in dependency_files.CONFIGURATION_FILES_GO


class TestConfigurationFilesRust:
    """Test CONFIGURATION_FILES_RUST constant."""

    def test_configuration_files_rust_is_list(self):
        """Test that CONFIGURATION_FILES_RUST is a list."""
        assert isinstance(dependency_files.CONFIGURATION_FILES_RUST, list)

    def test_configuration_files_rust_contains_cargo_toml(self):
        """Test that CONFIGURATION_FILES_RUST contains Cargo.toml."""
        assert "Cargo.toml" in dependency_files.CONFIGURATION_FILES_RUST


class TestConfigurationFilesSwift:
    """Test CONFIGURATION_FILES_SWIFT constant."""

    def test_configuration_files_swift_is_list(self):
        """Test that CONFIGURATION_FILES_SWIFT is a list."""
        assert isinstance(dependency_files.CONFIGURATION_FILES_SWIFT, list)

    def test_configuration_files_swift_contains_package_swift(self):
        """Test that CONFIGURATION_FILES_SWIFT contains Package.swift."""
        assert "Package.swift" in dependency_files.CONFIGURATION_FILES_SWIFT


class TestConfigurationFilesElixir:
    """Test CONFIGURATION_FILES_ELIXIR constant."""

    def test_configuration_files_elixir_is_list(self):
        """Test that CONFIGURATION_FILES_ELIXIR is a list."""
        assert isinstance(dependency_files.CONFIGURATION_FILES_ELIXIR, list)

    def test_configuration_files_elixir_contains_mix_exs(self):
        """Test that CONFIGURATION_FILES_ELIXIR contains mix.exs."""
        assert "mix.exs" in dependency_files.CONFIGURATION_FILES_ELIXIR


class TestConfigurationFilesHaskell:
    """Test CONFIGURATION_FILES_HASKELL constant."""

    def test_configuration_files_haskell_is_list(self):
        """Test that CONFIGURATION_FILES_HASKELL is a list."""
        assert isinstance(dependency_files.CONFIGURATION_FILES_HASKELL, list)

    def test_configuration_files_haskell_contains_package_yaml(self):
        """Test that CONFIGURATION_FILES_HASKELL contains package.yaml."""
        assert "package.yaml" in dependency_files.CONFIGURATION_FILES_HASKELL


class TestConfigurationFilesShell:
    """Test CONFIGURATION_FILES_SHELL constant."""

    def test_configuration_files_shell_is_list(self):
        """Test that CONFIGURATION_FILES_SHELL is a list."""
        assert isinstance(dependency_files.CONFIGURATION_FILES_SHELL, list)

    def test_configuration_files_shell_contains_rc_files(self):
        """Test that CONFIGURATION_FILES_SHELL contains shell rc files."""
        assert ".bashrc" in dependency_files.CONFIGURATION_FILES_SHELL
        assert ".zshrc" in dependency_files.CONFIGURATION_FILES_SHELL


class TestConfigurationFilesAws:
    """Test CONFIGURATION_FILES_AWS constant."""

    def test_configuration_files_aws_is_list(self):
        """Test that CONFIGURATION_FILES_AWS is a list."""
        assert isinstance(dependency_files.CONFIGURATION_FILES_AWS, list)

    def test_configuration_files_aws_contains_terraform(self):
        """Test that CONFIGURATION_FILES_AWS contains Terraform files."""
        assert "*.tf" in dependency_files.CONFIGURATION_FILES_AWS
        assert "terraform.tfstate" in dependency_files.CONFIGURATION_FILES_AWS


class TestConfigurationFilesDocker:
    """Test CONFIGURATION_FILES_DOCKER constant."""

    def test_configuration_files_docker_is_list(self):
        """Test that CONFIGURATION_FILES_DOCKER is a list."""
        assert isinstance(dependency_files.CONFIGURATION_FILES_DOCKER, list)

    def test_configuration_files_docker_contains_dockerfile(self):
        """Test that CONFIGURATION_FILES_DOCKER contains Dockerfile."""
        assert "Dockerfile" in dependency_files.CONFIGURATION_FILES_DOCKER

    def test_configuration_files_docker_contains_compose_files(self):
        """Test that CONFIGURATION_FILES_DOCKER contains docker-compose files."""
        assert "docker-compose.yml" in dependency_files.CONFIGURATION_FILES_DOCKER
        assert "docker-compose.yaml" in dependency_files.CONFIGURATION_FILES_DOCKER


class TestConfigurationFiles:
    """Test the main CONFIGURATION_FILES constant."""

    def test_configuration_files_is_list(self):
        """Test that CONFIGURATION_FILES is a list."""
        assert isinstance(dependency_files.CONFIGURATION_FILES, list)

    def test_configuration_files_not_empty(self):
        """Test that CONFIGURATION_FILES is not empty."""
        assert len(dependency_files.CONFIGURATION_FILES) > 0

    def test_configuration_files_contains_all_sublists(self):
        """Test that CONFIGURATION_FILES contains all files from sublists."""
        # Test that files from each sublist are present in the main list
        for css_file in dependency_files.CONFIGURATION_FILES_CSS:
            assert css_file in dependency_files.CONFIGURATION_FILES

        for next_file in dependency_files.CONFIGURATION_FILES_NEXT:
            assert next_file in dependency_files.CONFIGURATION_FILES

        for js_file in dependency_files.CONFIGURATION_FILES_JS:
            assert js_file in dependency_files.CONFIGURATION_FILES

        for python_file in dependency_files.CONFIGURATION_FILES_PYTHON:
            assert python_file in dependency_files.CONFIGURATION_FILES

    def test_configuration_files_contains_additional_files(self):
        """Test that CONFIGURATION_FILES contains additional language-specific files."""
        additional_files = [
            "pubspec.yaml",  # Dart/Flutter
            "DESCRIPTION",   # R
            "build.sbt",     # Scala
            "project.clj",   # Clojure
            "rebar.config",  # Erlang
            "dune-project",  # OCaml
            "*.opam",        # OCaml
            "*.nimble",      # Nim
        ]
        for additional_file in additional_files:
            assert additional_file in dependency_files.CONFIGURATION_FILES

    def test_configuration_files_no_duplicates(self):
        """Test that CONFIGURATION_FILES has no duplicate entries."""
        files_list = dependency_files.CONFIGURATION_FILES
        assert len(files_list) == len(set(files_list))

    def test_configuration_files_all_strings(self):
        """Test that all items in CONFIGURATION_FILES are strings."""
        for file_item in dependency_files.CONFIGURATION_FILES:
            assert isinstance(file_item, str)
            assert len(file_item) > 0  # No empty strings


class TestModuleStructure:
    """Test the overall structure of the dependency_files module."""

    def test_all_constants_are_lists(self):
        """Test that all configuration file constants are lists."""
        constant_names = [
            "CONFIGURATION_FILES_CSS",
            "CONFIGURATION_FILES_NEXT",
            "CONFIGURATION_FILES_JS",
            "CONFIGURATION_FILES_PYTHON",
            "CONFIGURATION_FILES_RUBY",
            "CONFIGURATION_FILES_PHP",
            "CONFIGURATION_FILES_JAVA",
            "CONFIGURATION_FILES_C",
            "CONFIGURATION_FILES_DOTNET",
            "CONFIGURATION_FILES_GO",
            "CONFIGURATION_FILES_RUST",
            "CONFIGURATION_FILES_SWIFT",
            "CONFIGURATION_FILES_ELIXIR",
            "CONFIGURATION_FILES_HASKELL",
            "CONFIGURATION_FILES_SHELL",
            "CONFIGURATION_FILES_AWS",
            "CONFIGURATION_FILES_DOCKER",
            "CONFIGURATION_FILES",
        ]

        for constant_name in constant_names:
            constant_value = getattr(dependency_files, constant_name)
            assert isinstance(constant_value, list), f"{constant_name} should be a list"

    def test_module_has_expected_constants(self):
        """Test that the module has all expected constants."""
        expected_constants = [
            "CONFIGURATION_FILES_CSS",
            "CONFIGURATION_FILES_NEXT",
            "CONFIGURATION_FILES_JS",
            "CONFIGURATION_FILES_PYTHON",
            "CONFIGURATION_FILES_RUBY",
            "CONFIGURATION_FILES_PHP",
            "CONFIGURATION_FILES_JAVA",
            "CONFIGURATION_FILES_C",
            "CONFIGURATION_FILES_DOTNET",
            "CONFIGURATION_FILES_GO",
            "CONFIGURATION_FILES_RUST",
            "CONFIGURATION_FILES_SWIFT",
            "CONFIGURATION_FILES_ELIXIR",
            "CONFIGURATION_FILES_HASKELL",
            "CONFIGURATION_FILES_SHELL",
            "CONFIGURATION_FILES_AWS",
            "CONFIGURATION_FILES_DOCKER",
            "CONFIGURATION_FILES",
        ]

        for constant_name in expected_constants:
            assert hasattr(dependency_files, constant_name), f"Module should have {constant_name}"

    def test_constants_are_not_empty(self):
        """Test that all configuration file constants are not empty."""
        constant_names = [
            "CONFIGURATION_FILES_CSS",
            "CONFIGURATION_FILES_NEXT",
            "CONFIGURATION_FILES_JS",
            "CONFIGURATION_FILES_PYTHON",
            "CONFIGURATION_FILES_RUBY",
            "CONFIGURATION_FILES_PHP",
            "CONFIGURATION_FILES_JAVA",
            "CONFIGURATION_FILES_C",
            "CONFIGURATION_FILES_DOTNET",
            "CONFIGURATION_FILES_GO",
            "CONFIGURATION_FILES_RUST",
            "CONFIGURATION_FILES_SWIFT",
            "CONFIGURATION_FILES_ELIXIR",
            "CONFIGURATION_FILES_HASKELL",
            "CONFIGURATION_FILES_SHELL",
            "CONFIGURATION_FILES_AWS",
            "CONFIGURATION_FILES_DOCKER",
            "CONFIGURATION_FILES",
        ]

        for constant_name in constant_names:
            constant_value = getattr(dependency_files, constant_name)
            assert len(constant_value) > 0, f"{constant_name} should not be empty"
