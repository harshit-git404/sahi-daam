"""
inspection_control/api/server.py
FastAPI Web Server for Tabletop Inspection Control Station.
"""

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from inspection_control.api.routes import router as station_router

app = FastAPI(
    title="Tabletop Inspection Station Control System",
    description="Closed-Loop Physical Inspection Controller for Bulk Perishable Lots",
    version="1.0.0",
)

app.include_router(station_router)

static_dir = os.path.join(os.path.dirname(__file__), "..", "ui", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def serve_dashboard():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Inspection Control Station API Active"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("inspection_control.api.server:app", host="0.0.0.0", port=8001, reload=True)
