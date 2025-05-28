#!/usr/bin/env python3
"""
Simple test runner to verify the github_utils tests can be imported and run.
This helps validate that all dependencies are correctly set up.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

try:
    # Test imports
    from services.github.test_github_utils import TestCreatePermissionUrl, TestDeconstructGitHubPayload
    from services.github.test_github_utils_integration import TestDeconstructGitHubPayloadIntegration
    
    print("✅ All imports successful!")
    print("✅ Test classes found:")
    print(f"   - TestCreatePermissionUrl: {len([m for m in dir(TestCreatePermissionUrl) if m.startswith('test_')])} test methods")
    print(f"   - TestDeconstructGitHubPayload: {len([m for m in dir(TestDeconstructGitHubPayload) if m.startswith('test_')])} test methods")
    print(f"   - TestDeconstructGitHubPayloadIntegration: {len([m for m in dir(TestDeconstructGitHubPayloadIntegration) if m.startswith('test_')])} test methods")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)

print("\n🎉 All tests are ready to run!")
print("Run with: python -m pytest services/github/test_github_utils.py -v")
print("Run integration tests with: python -m pytest services/github/test_github_utils_integration.py -v")
