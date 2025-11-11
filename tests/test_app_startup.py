from fastapi.testclient import TestClient
from app.main import app # Assuming your FastAPI app object is in app/main.py

client = TestClient(app)

def test_app_starts_and_health_check_passes():
    """
    A simple smoke test to ensure the app can start and respond.
    """
    response = client.get("/") # Or a dedicated "/health" endpoint
    # Check if the app responds with a successful status code (like 200 OK)
    assert response.status_code == 200
    # You could also check for a simple message
    # assert response.json() == {"message": "Welcome to OELP!"}