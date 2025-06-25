#!/usr/bin/env python3
"""
Test script to verify that all imports work correctly for the new test files.
"""

def test_imports():
    """Test that all imports work correctly."""
    try:
        # Test chat_with_agent imports
        from services.chat_with_agent import chat_with_agent
        from config import OPENAI_MODEL_ID_O3_MINI
        print("✓ chat_with_agent imports work")
        
        # Test webhook handler imports
        from services.webhook.check_run_handler import handle_check_run
        from services.webhook.issue_handler import create_pr_from_issue
        from services.webhook.push_handler import handle_push_event
        from services.webhook.review_run_handler import handle_review_run
        print("✓ webhook handler imports work")
        
        # Test config imports
        from config import GITHUB_APP_USER_NAME, STRIPE_PRODUCT_ID_FREE, EXCEPTION_OWNERS, PRODUCT_ID
        print("✓ config imports work")
        
        # Test find_pull_request_by_branch import
        from services.github.pull_requests.find_pull_request_by_branch import find_pull_request_by_branch
        print("✓ find_pull_request_by_branch import works")
        
        print("\n✅ All imports successful!")
        assert True  # All imports successful
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        assert False, f"Import error: {e}"
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        assert False, f"Unexpected error: {e}"

if __name__ == "__main__":
    test_imports()
    print("Test completed successfully!")
