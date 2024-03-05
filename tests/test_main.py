import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "PR Agent APP"}

def test_webhook_signature_verification_error():
    response = client.post("/webhook", json={})
    assert response.status_code == 500
    assert "detail" in response.json()
    assert response.json()["detail"] == "Error: HTTPException(status_code=500, detail='Error: signature verification failed')"

