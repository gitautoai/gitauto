--- /dev/null
+++ tests/test_main.py
@@ -0,0 +1,24 @@
+import json
+from starlette.testclient import TestClient
+
+from main import app
+
+client = TestClient(app)
+
+def test_webhook():
+    response = client.post("/webhook", json={"test": "data"})
+    assert response.status_code == 200
+    assert response.json() == {"message": "Webhook processed successfully"}
+
+def test_root():
+    response = client.get("/")
+    assert response.status_code == 200
+    assert response.json() == {"message": "PR Agent APP"}
+
+def test_invalid_webhook():
+    response = client.post("/webhook", json={})
+    assert response.status_code == 500
+    assert "detail" in response.json()
+    assert response.json()["detail"] == "Error: 'NoneType' object has no attribute 'headers'"
