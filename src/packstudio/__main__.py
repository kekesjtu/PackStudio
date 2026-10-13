"""PackStudio 后端命令行入口。

桌面宿主（WebView2）与 PyInstaller 打包共用同一入口，使开发与打包后的
启动参数保持一致：python -m packstudio --port <port>。
"""

import argparse

import uvicorn

from packstudio.api.app import app


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="packstudio-backend",
        description="PackStudio 本地 API 服务",
    )
    parser.add_argument("--host", default="127.0.0.1", help="监听地址（默认 127.0.0.1）")
    parser.add_argument("--port", type=int, default=8000, help="监听端口（默认 8000）")
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
