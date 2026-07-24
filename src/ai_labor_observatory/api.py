from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware


def create_app(data_dir: Path = Path("data/sample")) -> FastAPI:
    app = FastAPI(
        title="AI Labor Observatory API",
        version="0.1.0",
        description="Evidence-backed AI labor-market indicators.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/summary")
    def summary() -> dict[str, object]:
        path = data_dir / "summary.json"
        if not path.exists():
            raise HTTPException(503, "Build data artifacts before starting the API")
        return json.loads(path.read_text(encoding="utf-8"))

    @app.get("/api/occupations")
    def occupations(
        minimum_ai_intensity: float = Query(0, ge=0, le=100),
        limit: int = Query(50, ge=1, le=250),
    ) -> list[dict[str, object]]:
        path = data_dir / "occupation_metrics.csv"
        if not path.exists():
            raise HTTPException(503, "Build data artifacts before starting the API")
        frame = pd.read_csv(path)
        filtered = frame[frame["ai_intensity"] >= minimum_ai_intensity]
        filtered = filtered.sort_values("ai_intensity", ascending=False).head(limit)
        return json.loads(filtered.to_json(orient="records"))

    return app


app = create_app()
