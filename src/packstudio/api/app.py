from fastapi import FastAPI


def create_app() -> FastAPI:
    application = FastAPI(
        title="PackStudio API",
        description="IC package parametric thermal-model service",
        version="0.1.0",
    )

    @application.get("/api/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "packstudio"}

    return application


app = create_app()
