from fastapi import FastAPI
from routers import scan, haggle

app = FastAPI(title="Sahi Daam API")

app.include_router(scan.router)
app.include_router(haggle.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
