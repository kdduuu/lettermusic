
from fastapi.testclient import TestClient
from backend.app.main import app

# Permite testar nossa API sem iniciar o servidor manualmente.
client = TestClient(app)


def test_health():
    resposta = client.get("/health")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}
