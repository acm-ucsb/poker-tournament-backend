from fastapi.testclient import TestClient
from src.main import app

def test_basic():
    client = TestClient(app)
    with client.websocket_connect("/game/2/ws") as websocket:
        data = websocket.receive_text()
        assert data == "Game state changed!"