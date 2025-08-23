"""Unit tests for __init__.py module."""

import importlib
import importlib.util
import os
import sys
from types import ModuleType

import pytest


class TestInitModule:
    """Test cases for the root __init__.py module."""

    def test_module_can_be_imported(self):
        """Test that the root package can be imported without errors."""
        try:
            # Import the current directory as a package
            spec = importlib.util.spec_from_file_location("gitauto", "__init__.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            assert module is not None
        except ImportError as e:
            pytest.fail(f"Failed to import root package: {e}")
        except Exception as e:
            pytest.fail(f"Unexpected error importing root package: {e}")

    def test_init_file_exists(self):
        """Test that __init__.py file exists in the current directory."""
        assert os.path.exists("__init__.py")
        assert os.path.isfile("__init__.py")

    def test_init_file_is_empty_or_minimal(self):
        """Test that __init__.py file is empty or contains minimal content."""
        with open("__init__.py", "r", encoding="utf-8") as f:
            content = f.read().strip()
        
        # The file should be empty or contain only whitespace/comments
        # Remove comments and whitespace to check if there's actual code
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        code_lines = [line for line in lines if not line.startswith('#')]
        
        assert len(code_lines) == 0, f"Expected empty __init__.py but found code: {code_lines}"

    def test_init_file_syntax_is_valid(self):
        """Test that __init__.py has valid Python syntax."""
        try:
            with open("__init__.py", "r", encoding="utf-8") as f:
                content = f.read()
            compile(content, "__init__.py", "exec")
        except SyntaxError as e:
            pytest.fail(f"__init__.py has invalid syntax: {e}")

    def test_module_creates_no_public_exports(self):
        """Test that importing the module doesn't create unexpected public exports."""
        spec = importlib.util.spec_from_file_location("test_gitauto", "__init__.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Get all attributes that don't start with underscore (public attributes)
        public_attrs = [attr for attr in dir(module) if not attr.startswith('_')]
        
        # Empty __init__.py should not have any public exports
        assert len(public_attrs) == 0, f"Unexpected public attributes found: {public_attrs}"

    def test_module_execution_completes_without_error(self):
        """Test that executing the __init__.py module completes without errors."""
        spec = importlib.util.spec_from_file_location("test_execution", "__init__.py")
        module = importlib.util.module_from_spec(spec)
        
        # This should not raise any exceptions
        spec.loader.exec_module(module)
        assert isinstance(module, ModuleType)

    def test_module_has_standard_attributes(self):
        """Test that the module has standard Python module attributes."""
        spec = importlib.util.spec_from_file_location("test_attrs", "__init__.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Standard module attributes that should exist
        assert hasattr(module, '__name__')
        assert hasattr(module, '__file__')
        assert hasattr(module, '__doc__')
        
        # Verify attributes have expected types
        assert isinstance(module.__name__, str)
        assert module.__file__ is None or isinstance(module.__file__, str)
        assert module.__doc__ is None or isinstance(module.__doc__, str)

    def test_module_file_size_is_minimal(self):
        """Test that __init__.py file size is minimal (empty or nearly empty)."""
        file_size = os.path.getsize("__init__.py")
        
        # File should be very small (empty or just whitespace)
        # Allow up to 10 bytes for potential whitespace/newlines
        assert file_size <= 10, f"__init__.py file size is {file_size} bytes, expected <= 10"

    def test_module_import_does_not_modify_globals(self):
        """Test that importing the module doesn't modify global namespace."""
        # Capture current globals
        original_globals = set(globals().keys())
        
        # Import the module
        spec = importlib.util.spec_from_file_location("test_globals", "__init__.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Check that globals haven't changed
        current_globals = set(globals().keys())
        new_globals = current_globals - original_globals
        
        # Only allow the module variable itself to be added
        expected_new_globals = {'module', 'spec'}  # These are local variables from this test
        unexpected_globals = new_globals - expected_new_globals
        
        assert len(unexpected_globals) == 0, f"Unexpected globals added: {unexpected_globals}"

    def test_module_import_is_idempotent(self):
        """Test that importing the module multiple times is safe."""
        modules = []
        
        # Import the module multiple times
        for i in range(3):
            spec = importlib.util.spec_from_file_location(f"test_idempotent_{i}", "__init__.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            modules.append(module)
        
        # All modules should be valid ModuleType instances
        for module in modules:
            assert isinstance(module, ModuleType)
            
        # Each import creates a new module instance (expected behavior)
        # but they should all have the same basic properties
        for module in modules:
            assert hasattr(module, '__name__')
            assert hasattr(module, '__file__')
            assert hasattr(module, '__doc__')