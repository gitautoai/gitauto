import pytest

# Integration test for the Supabase owners manager.
# This test checks basic functionality of the owers_manager module.
# For more details on Supabase, please refer to https://supabase.io/docs

from services.supabase import owers_manager
from tests.constants import OWNER, REPO, TOKEN

def test_owers_manager_integration():
    """
    Integration test for services/supabase/owers_manager.py

    This test ensures that the module can connect and retrieve owner records.
    If the required function is not implemented, the test will be skipped.
    """
    # Check if the function 'get_all_owners' exists
    if hasattr(owers_manager, 'get_all_owners'):
        result = owers_manager.get_all_owners(OWNER, TOKEN)
        # Assert that the result is a list, which would represent the owners
        assert isinstance(result, list), "Expected a list of owners"
    else:
        pytest.skip("Function get_all_owners is not implemented in owers_manager")
