"""Unit tests for __init__.py module."""

import importlib
import sys
from types import ModuleType

import pytest


class TestInitModule:
    """Test cases for the root __init__.py module."""

    def test_module_can_be_imported(self):
        """Test that __init__.py can be imported without errors."""
        try:
            import __init__
            assert __init__ is not None
        except ImportError as e:
            pytest.fail(f"Failed to import __init__ module: {e}")

    def test_module_is_module_type(self):
        """Test that imported __init__ is a proper module type."""
        import __init__
        assert isinstance(__init__, ModuleType)

    def test_module_has_expected_attributes(self):
        """Test that __init__ module has standard module attributes."""
        import __init__
        
        # Standard module attributes that should exist
        assert hasattr(__init__, '__name__')
        assert hasattr(__init__, '__file__')
        assert hasattr(__init__, '__doc__')
        
        # Verify __name__ is correct
        assert __init__.__name__ == '__init__'

    def test_module_has_no_public_exports(self):
        """Test that __init__ module doesn't export any public attributes."""
        import __init__
        
        # Get all attributes that don't start with underscore (public attributes)
        public_attrs = [attr for attr in dir(__init__) if not attr.startswith('_')]
        
        # Empty __init__.py should not have any public exports
        assert len(public_attrs) == 0, f"Unexpected public attributes found: {public_attrs}"

    def test_module_reimport_consistency(self):
        """Test that reimporting the module returns the same object."""
        import __init__ as init1
        
        # Remove from sys.modules to force reimport
        if '__init__' in sys.modules:
            del sys.modules['__init__']
        
        import __init__ as init2
        
        # Both imports should refer to the same module type
        assert type(init1) == type(init2)
        assert isinstance(init1, ModuleType)
        assert isinstance(init2, ModuleType)

    def test_module_importlib_import(self):
        """Test that module can be imported using importlib."""
        module = importlib.import_module('__init__')
        assert module is not None
        assert isinstance(module, ModuleType)
        assert module.__name__ == '__init__'

    def test_module_file_path_exists(self):
        """Test that module __file__ attribute points to existing file."""
        import __init__
        import os
        
        assert __init__.__file__ is not None
        assert os.path.exists(__init__.__file__)
        assert __init__.__file__.endswith('__init__.py')

    def test_module_docstring_is_none_or_string(self):
        """Test that module docstring is None or a string."""
        import __init__
        
        docstring = __init__.__doc__
        assert docstring is None or isinstance(docstring, str)

    def test_module_in_sys_modules(self):
        """Test that module is properly registered in sys.modules after import."""
        import __init__
        
        assert '__init__' in sys.modules
        assert sys.modules['__init__'] is __init__
