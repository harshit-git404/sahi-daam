from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import scan, haggle

app = FastAPI(title="Sahi Daam API")

app.add_middleware(
    CORSMiddleware,
    # TODO: Tighten CORS before real deployment
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(scan.router)
app.include_router(haggle.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
