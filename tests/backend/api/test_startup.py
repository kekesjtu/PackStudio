from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from fastapi.testclient import TestClient

from packstudio.api.app import app
from packstudio.templates.package_library import catalog as registry


def test_parallel_initial_requests_share_one_template_initialization(monkeypatch) -> None:
    registry.definitions.cache_clear()
    original = registry.cbga_fc.definition
    initialized = []

    def tracked_definition():
        result = original()
        initialized.append(result)
        return result

    monkeypatch.setattr(registry.cbga_fc, "definition", tracked_definition)
    paths = (
        "/api/templates",
        "/api/templates/cbga_fc/schema",
        "/api/templates/cbga_fc/defaults",
    )
    barrier = Barrier(len(paths))
    try:
        with TestClient(app) as client:

            def load(path):
                barrier.wait(timeout=10)
                return client.get(path)

            with ThreadPoolExecutor(max_workers=len(paths)) as workers:
                responses = list(workers.map(load, paths))
            assert [response.status_code for response in responses] == [200, 200, 200]
            assert len(initialized) == 1
            assert len(responses[0].json()) == 8
            generated = client.post("/api/templates/cbga_fc/generate", json=responses[2].json())
            assert generated.status_code == 200
            assert generated.json()["blocks"]
    finally:
        registry.definitions.cache_clear()
