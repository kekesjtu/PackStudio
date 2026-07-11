from fastapi import FastAPI

from packstudio.api.routes.templates import router as templates_router


def create_app() -> FastAPI:
    application = FastAPI(
        title="PackStudio API",
        description="IC package parametric thermal-model service",
        version="0.1.0",
    )

    @application.get("/api/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "packstudio"}

    application.include_router(templates_router)
    return application


app = create_app()
