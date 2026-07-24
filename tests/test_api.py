import json
from pathlib import Path

from fastapi.testclient import TestClient

from ai_labor_observatory.api import create_app


def test_api_serves_summary_and_filtered_occupations(tmp_path: Path) -> None:
    (tmp_path / "summary.json").write_text(
        json.dumps({"title": "AI Labor Observatory"}), encoding="utf-8"
    )
    (tmp_path / "occupation_metrics.csv").write_text(
        "soc_code,occupation_title,ai_intensity\n"
        "152051,Data Scientists,22.5\n"
        "439199,Office Support,1.0\n",
        encoding="utf-8",
    )
    client = TestClient(create_app(tmp_path))

    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/api/summary").json()["title"] == "AI Labor Observatory"
    rows = client.get("/api/occupations?minimum_ai_intensity=10").json()
    assert [row["soc_code"] for row in rows] == [152051]
