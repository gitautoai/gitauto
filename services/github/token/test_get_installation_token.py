import requests
import pytest

from services.github.token.get_installation_token import get_installation_access_token


# Fake response object to simulate requests responses
class FakeResponse:
    def __init__(self, status_code, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data
        self.text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            http_err = requests.exceptions.HTTPError()
            http_err.response = self
            raise http_err

    def json(self):
        return self._json


# Test happy path: valid response returns token
def test_happy_path(monkeypatch):
    monkeypatch.setattr("services.github.token.get_installation_token.get_jwt", lambda: "fake_jwt")
    monkeypatch.setattr("services.github.token.get_installation_token.create_headers", lambda token: {"Auth": token})

    def fake_post(url, headers, timeout):
        assert "fake_jwt" in headers["Auth"]
        return FakeResponse(200, {"token": "installation_token"})

    monkeypatch.setattr(requests, "post", fake_post)

    token = get_installation_access_token(123)
    assert token == "installation_token"


# Test suspended installation: HTTPError with 403 and suspended message
def test_suspended_installation(monkeypatch):
    call_flag = {"called": False}

    def fake_delete_installation(installation_id, user_id, user_name):
        call_flag["called"] = True

    monkeypatch.setattr("services.github.token.get_installation_token.delete_installation", fake_delete_installation)
    monkeypatch.setattr("services.github.token.get_installation_token.get_jwt", lambda: "fake_jwt")
    monkeypatch.setattr("services.github.token.get_installation_token.create_headers", lambda token: {"Auth": token})

    def fake_post(url, headers, timeout):
        return FakeResponse(403, {"token": "dummy"}, "This installation has been suspended")

    monkeypatch.setattr(requests, "post", fake_post)

    with pytest.raises(requests.exceptions.HTTPError):
        get_installation_access_token(456)

    assert call_flag["called"]


# Test other HTTP errors: do not call delete_installation and simply raise error
def test_other_http_error(monkeypatch):
    call_flag = {"called": False}

    def fake_delete_installation(installation_id, user_id, user_name):
        call_flag["called"] = True

    monkeypatch.setattr("services.github.token.get_installation_token.delete_installation", fake_delete_installation)
    monkeypatch.setattr("services.github.token.get_installation_token.get_jwt", lambda: "fake_jwt")
    monkeypatch.setattr("services.github.token.get_installation_token.create_headers", lambda token: {"Auth": token})

    def fake_post(url, headers, timeout):
        return FakeResponse(404, {"error": "Not Found"}, "Not Found")

    monkeypatch.setattr(requests, "post", fake_post)

    with pytest.raises(requests.exceptions.HTTPError):
        get_installation_access_token(789)

    assert not call_flag["called"]
