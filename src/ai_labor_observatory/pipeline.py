from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from .analysis import build_skill_trends, fit_wage_model, summarize_geography
from .bls import STATE_AREAS, BlsClient
from .onet import (
    build_occupation_metrics,
    build_task_complements,
    load_education,
    load_job_zones,
)
from .taxonomy import TAXONOMY, TransparentSkillClassifier

FEATURED_SOCS = ("151221", "151252", "152051", "151211", "151232")


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return json.loads(frame.to_json(orient="records"))


def build_observatory(
    previous_dir: Path,
    current_dir: Path,
    output_dir: Path,
    previous_release: str = "O*NET 29.3 (May 2025)",
    current_release: str = "O*NET 30.3 (May 2026)",
    wage_year: int = 2025,
    occupation_limit: int = 120,
    registration_key: str | None = None,
    offline: bool = False,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    classifier = TransparentSkillClassifier()
    previous = build_occupation_metrics(previous_dir, previous_release, classifier)
    current = build_occupation_metrics(current_dir, current_release, classifier)
    education = load_education(current_dir)
    zones = load_job_zones(current_dir)
    current = current.merge(education, on="soc_code", how="left").merge(
        zones, on="soc_code", how="left"
    )
    trends = build_skill_trends(previous, current)
    task_complements = build_task_complements(current_dir, current)

    ranked = current.sort_values(
        ["ai_intensity", "total_software_skills"], ascending=False
    )
    comparison = current.sort_values("ai_intensity").head(max(20, occupation_limit // 4))
    selected = pd.concat(
        [ranked.head(occupation_limit), comparison], ignore_index=True
    ).drop_duplicates("soc_code")
    selected_socs = selected["soc_code"].tolist()

    national_cache_path = output_dir / "bls_national.csv"
    if national_cache_path.exists():
        national_cache = pd.read_csv(national_cache_path, dtype={"soc_code": str})
    elif (output_dir / "occupation_metrics.csv").exists():
        national_cache = pd.read_csv(
            output_dir / "occupation_metrics.csv", dtype={"soc_code": str}
        )[
            [
                "soc_code",
                "area_code",
                "area_name",
                "year",
                "employment",
                "annual_median_wage",
            ]
        ]
    else:
        national_cache = pd.DataFrame()
    if not national_cache.empty:
        national_cache["soc_code"] = national_cache["soc_code"].astype(str).str.zfill(6)
        national_cache["area_code"] = national_cache["area_code"].astype(str).str.zfill(7)
    cached_socs = set(national_cache.get("soc_code", pd.Series(dtype=str)).astype(str))
    missing_socs = [soc for soc in selected_socs if soc not in cached_socs]

    geography_cache_path = output_dir / "bls_geography.csv"
    if geography_cache_path.exists():
        geography_cache = pd.read_csv(geography_cache_path, dtype={"soc_code": str})
    elif (output_dir / "geography.csv").exists():
        geography_cache = pd.read_csv(output_dir / "geography.csv", dtype={"soc_code": str})[
            [
                "soc_code",
                "area_code",
                "area_name",
                "year",
                "employment",
                "annual_median_wage",
            ]
        ]
    else:
        geography_cache = pd.DataFrame()
    if not geography_cache.empty:
        geography_cache["soc_code"] = geography_cache["soc_code"].astype(str).str.zfill(6)
        geography_cache["area_code"] = geography_cache["area_code"].astype(str).str.zfill(7)
    featured = [soc for soc in FEATURED_SOCS if soc in set(current["soc_code"])]
    geography_expected = {(soc, area) for soc in featured for area in STATE_AREAS}
    geography_cached = {
        (str(row.soc_code), str(row.area_code).zfill(7))
        for row in geography_cache.itertuples()
    }
    geography_complete = geography_expected.issubset(geography_cached)

    if (missing_socs or not geography_complete) and not offline:
        with BlsClient(registration_key or os.getenv("BLS_REGISTRATION_KEY")) as client:
            fetched_national = (
                client.fetch(missing_socs, wage_year)
                if missing_socs
                else pd.DataFrame()
            )
            fetched_geography = (
                client.fetch(featured, wage_year, STATE_AREAS)
                if not geography_complete
                else pd.DataFrame()
            )
    else:
        fetched_national = pd.DataFrame()
        fetched_geography = pd.DataFrame()

    national = (
        pd.concat([national_cache, fetched_national], ignore_index=True)
        .drop_duplicates(["soc_code", "area_code"], keep="last")
    )
    national = national[national["soc_code"].isin(selected_socs)]
    if national.empty:
        raise RuntimeError(
            "No cached BLS observations are available. Run without offline mode "
            "or provide a populated output directory."
        )
    geography = (
        pd.concat([geography_cache, fetched_geography], ignore_index=True)
        .drop_duplicates(["soc_code", "area_code"], keep="last")
    )
    geography = geography[geography["soc_code"].isin(featured)]
    national.to_csv(national_cache_path, index=False)
    geography.to_csv(geography_cache_path, index=False)

    occupations = current.merge(national, on="soc_code", how="inner")
    occupations = occupations.sort_values("ai_intensity", ascending=False)
    wage_model = fit_wage_model(occupations)
    geography = summarize_geography(geography, national)
    geography = geography.merge(
        current[["soc_code", "occupation_title", "ai_intensity"]],
        on="soc_code",
        how="left",
    )

    current_category_columns = [
        column for column in current.columns if column.startswith("skills_")
    ]
    skill_mix = []
    for column in current_category_columns:
        skill_mix.append(
            {
                "category": column.removeprefix("skills_"),
                "skills": int(current[column].sum()),
                "description": TAXONOMY[column.removeprefix("skills_")]["description"],
            }
        )

    top_occupations = occupations[
        [
            "soc_code",
            "occupation_title",
            "ai_intensity",
            "ai_skill_share",
            "annual_median_wage",
            "employment",
            "bachelors_plus_share",
            "job_zone",
            "signal_occupation_titles",
        ]
    ].head(20)
    movers = trends[
        [
            "soc_code",
            "occupation_title",
            "previous_ai_intensity",
            "current_ai_intensity",
            "intensity_change",
        ]
    ].head(20)

    summary: dict[str, Any] = {
        "title": "AI Labor Observatory",
        "generated_at": datetime.now(UTC).isoformat(),
        "releases": {
            "previous": previous_release,
            "current": current_release,
            "bls_oews": f"May {wage_year}",
        },
        "coverage": {
            "onet_occupations": int(current["soc_code"].nunique()),
            "wage_model_occupations": wage_model.observations,
            "states": len(STATE_AREAS),
            "featured_geographic_occupations": len(FEATURED_SOCS),
            "requested_occupations_missing_bls_cache": len(missing_socs) if offline else 0,
        },
        "headline_metrics": {
            "highest_ai_intensity": round(float(top_occupations["ai_intensity"].max()), 2),
            "occupations_with_ai_signal": int((current["ai_intensity"] > 0).sum()),
            "median_ai_intensity": round(float(current["ai_intensity"].median()), 2),
            "wage_model_r_squared": round(wage_model.r_squared, 3),
        },
        "wage_model": wage_model.as_dict(),
        "top_occupations": _records(top_occupations),
        "fastest_movers": _records(movers),
        "task_complements": _records(task_complements),
        "geography": _records(geography),
        "skill_mix": skill_mix,
        "methodology_notes": [
            "AI intensity is a transparent weighted share of O*NET software-skill signals.",
            "O*NET software-skill hot and in-demand flags are derived from employer job postings.",
            "The wage model is cross-sectional and descriptive; "
            "it does not identify a causal premium.",
            "Federal and proprietary postings are not redistributed.",
            "Suppressed or unavailable BLS estimates remain missing rather than being imputed.",
            (
                f"Offline build used cached BLS evidence; {len(missing_socs)} newly requested "
                "occupations were unavailable in the cache."
                if offline and missing_socs
                else "The build used all requested BLS observations available from the API."
            ),
        ],
    }

    occupations.to_csv(output_dir / "occupation_metrics.csv", index=False)
    trends.to_csv(output_dir / "skill_trends.csv", index=False)
    task_complements.to_csv(output_dir / "task_complements.csv", index=False)
    geography.to_csv(output_dir / "geography.csv", index=False)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return summary
