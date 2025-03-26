from main import app


def test_endpoints_should_not_start_with_api():
    """Test that no endpoint paths start with /api

    AWS Lambda + API Gateway integration with FastAPI requires that
    endpoint paths do not start with /api, as API Gateway automatically
    adds this prefix to all routes.

    Examples:
        Good:
            @app.get("/users")     -> API Gateway: /api/users
            @app.post("/webhook")   -> API Gateway: /api/webhook

        Bad:
            @app.get("/api/users")  -> API Gateway: /api/api/users
            @app.post("/api/webhook") -> API Gateway: /api/api/webhook
    """
    routes = app.routes
    for route in routes:
        assert not route.path.startswith(
            "/api"
        ), f"Endpoint {route.path} should not start with /api"
