from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes.websocket import router as websocket_router
from app.api.routes.smart_home import router as smart_home_router
from app.core.logging_config import setup_logging


def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(title="IoT Smart Home Backend")
    app.include_router(websocket_router)
    app.include_router(smart_home_router)

    frontend_dir = Path(__file__).resolve().parent / "frontend"
    if frontend_dir.exists():
        app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")

        @app.get("/", include_in_schema=False)
        async def serve_frontend() -> FileResponse:
            return FileResponse(frontend_dir / "index.html")
    else:

        @app.get("/", include_in_schema=False)
        async def root_message() -> JSONResponse:
            return JSONResponse({"message": "IoT Smart Home Backend"})
    return app


app = create_app()
