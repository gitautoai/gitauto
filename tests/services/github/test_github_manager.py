import time
import jwt
import unittest

from services.github import github_manager


class DummyJWT:
    def __init__(self):
        self.last_payload = None
        self.last_key = None
        self.last_alg = None

    def encode(self, payload, key, algorithm):
        self.last_payload = payload
        self.last_key = key
        self.last_alg = algorithm
        return "dummy.jwt.token"


class TestCreateJWT(unittest.TestCase):
    def test_create_jwt(self):
        # Patch time.time to return a fixed time
        fixed_time = 1000000
        original_time = time.time
        time.time = lambda: fixed_time

        # Patch jwt.encode to capture payload and return dummy token
        dummy_jwt = DummyJWT()
        original_jwt_encode = jwt.encode
        jwt.encode = dummy_jwt.encode

        # Override GITHUB_APP_ID and GITHUB_PRIVATE_KEY for testing
        original_app_id = getattr(github_manager, "GITHUB_APP_ID", None)
        original_private_key = getattr(github_manager, "GITHUB_PRIVATE_KEY", None)
        github_manager.GITHUB_APP_ID = "test_app_id"
        github_manager.GITHUB_PRIVATE_KEY = "test_private_key"

        token = github_manager.create_jwt()

        # Restore patched functions and variables
        time.time = original_time
        jwt.encode = original_jwt_encode
        github_manager.GITHUB_APP_ID = original_app_id
        github_manager.GITHUB_PRIVATE_KEY = original_private_key

        # Verify payload values and token
        self.assertEqual(dummy_jwt.last_payload["iat"], fixed_time)
        self.assertEqual(dummy_jwt.last_payload["exp"], fixed_time + 600)
        self.assertEqual(dummy_jwt.last_payload["iss"], "test_app_id")
        self.assertEqual(dummy_jwt.last_alg, "RS256")
        self.assertEqual(token, "dummy.jwt.token")


if __name__ == '__main__':
    unittest.main()
