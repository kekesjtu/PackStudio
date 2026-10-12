"""Measure a fresh backend's initial browser API requests (run in a new process)."""

import json
from concurrent.futures import ThreadPoolExecutor
from time import perf_counter


def main() -> None:
    started = perf_counter()
    from fastapi.testclient import TestClient

    from packstudio.api.app import app

    imported = perf_counter()
    paths = (
        "/api/templates",
        "/api/templates/cbga_fc/schema",
        "/api/templates/cbga_fc/defaults",
        "/api/templates/materials",
    )
    with TestClient(app) as client:
        with ThreadPoolExecutor(max_workers=len(paths)) as workers:
            responses = list(workers.map(client.get, paths))
        loaded = perf_counter()
        for response in responses:
            response.raise_for_status()
        generated = client.post("/api/templates/cbga_fc/generate", json=responses[2].json())
        generated.raise_for_status()
        finished = perf_counter()
    print(
        json.dumps(
            {
                "import_seconds": round(imported - started, 3),
                "initial_parallel_requests_seconds": round(loaded - imported, 3),
                "initial_generation_seconds": round(finished - loaded, 3),
                "total_seconds": round(finished - started, 3),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
