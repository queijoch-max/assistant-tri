from fastapi import FastAPI

app = FastAPI(title="Cycles Mistral - SAV")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/accueil")
def accueil() -> dict[str, str]:
    return {"message": "Bienvenue au SAV de Cycle Mistral"}
