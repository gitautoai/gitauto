from utils.error.handle_exceptions import handle_exceptions

# Dependency dirs we support caching as tarballs for faster installs
SUPPORTED_DEPENDENCY_DIRS = [
    "node_modules",  # npm/yarn/pnpm (JS/TS)
    "vendor",  # Composer (PHP), Go modules
]

# All third-party dependency directories by language/ecosystem (for file filtering)
DEPENDENCY_DIRS = SUPPORTED_DEPENDENCY_DIRS + [
    ".bundle",  # Bundler (Ruby)
    ".dart_tool",  # Dart/Flutter
    ".venv",  # virtualenv (Python, alternative)
    "bower_components",  # Bower (JS, legacy)
    "Carthage",  # Carthage (iOS)
    "deps",  # Mix (Elixir)
    "elm-stuff",  # Elm
    "Godeps",  # godep (Go, legacy)
    "jspm_packages",  # jspm (JS)
    "Packages",  # NuGet (C#), Swift Package Manager
    "Pods",  # CocoaPods (iOS)
    "venv",  # virtualenv (Python)
]


@handle_exceptions(default_return_value=False, raise_on_error=False)
def is_dependency_file(file_path: str):
    """Check if a file is under a third-party dependency directory."""
    parts = file_path.split("/")
    return any(part in DEPENDENCY_DIRS for part in parts)
