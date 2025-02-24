import time
import jwt
import pytest
from services.github import github_manager as gm

# This is a unit test for the create_jwt function in services/github/github_manager.py
# Related GitHub documentation: https://docs.github.com/en/developers/apps/authenticating-with-github-apps

def test_create_jwt():
    # Set up test RSA private key and test app id for JWT
    test_private_key = """-----BEGIN RSA PRIVATE KEY-----
MIIBOwIBAAJBAN/Uz+1lp5Blt2nLlWF226EKo1JwacYWU7czOZV+0QMFaFDJ9Uaf
7Y/k04h22+5k7beKkjji/rRDL5dBVWATwzECAwEAAQJBAI7AlHYifgkKKNHnce5BM
Z3+sNLZ2TVI1Hg3aYPZ2Eay2mmzrNZgPT2fYx2mXZz9HrzQxintJz9F0FeZKHyAP
k2ECIQD+M9aSdciiuUptpX1V3ph4YDwj/93imNGHA8FNdvliXQIhAN9oAyP+YCNz
NsksY6yat3WDGp5znvEdNbI7f0rFeILTAiAv/5cZ4sk0wP3JoX/Ev04L9E+HLBFk
ZkRD9EAkvFUp4QIhAJrTUu2eDbTIUzLLOgkTeF+ecebO9Dmi5TI+ac4bTiCBAiEA
kQPpdfn6BsJb6pIQBbVRiZkkK8lTwC10L+I/TM16iQ8=
-----END RSA PRIVATE KEY-----"""
    test_app_id = "123456"
    gm.GITHUB_PRIVATE_KEY = test_private_key
    gm.GITHUB_APP_ID = test_app_id

    # Record current time
    now = int(time.time())

    # Create JWT
    token = gm.create_jwt()

    # Assert that the token is a string and contains three parts separated by '.'
    assert isinstance(token, str)
    parts = token.split('.')
    assert len(parts) == 3

    # Decode token without verifying signature
    payload = jwt.decode(token, options={"verify_signature": False})
    assert payload["iss"] == test_app_id

    # Check that the token expires 600 seconds after it was issued
    assert payload["exp"] - payload["iat"] == 600

if __name__ == "__main__":
    pytest.main()
