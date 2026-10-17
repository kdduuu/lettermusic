
from fastapi import FastAPI

app = FastAPI(title="Lettermusic API")


@app.get("/health")
def verificar_saude():
    """Confirma que a API está respondendo."""
    return {"status": "ok"}
