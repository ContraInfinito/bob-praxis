"""Sample pytest test file for Praxis stack detection testing."""

from app import app


def test_hello_route():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"Hello from sample_python_project" in response.data

# Made with Bob
