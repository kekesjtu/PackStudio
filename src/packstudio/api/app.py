import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from packstudio.api.routes.templates import router as templates_router

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _mount_frontend(application: FastAPI) -> None:
    """托管前端静态产物，使桌面壳加载后端端口即可使用整个应用。

    dist 目录存在时才挂载；未构建前端时保持纯 API 服务。挂载在 API 路由
    之后注册，保证 /api 前缀优先匹配。
    """
    frontend_dir = Path(
        os.environ.get("PACKSTUDIO_FRONTEND_DIR", str(_REPO_ROOT / "dist"))
    )
    if frontend_dir.is_dir():
        application.mount(
            "/", StaticFiles(directory=frontend_dir, html=True), name="frontend"
        )


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
    _mount_frontend(application)
    return application


app = create_app()
