from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .tasks import classify_task
from .taxonomy import NON_AI_LABEL, TransparentSkillClassifier, taxonomy_weight


def _find(directory: Path, filename: str) -> Path:
    matches = list(directory.rglob(filename))
    if not matches:
        raise FileNotFoundError(f"Could not find {filename!r} below {directory}")
    return matches[0]


def normalize_soc(value: str) -> str:
    """Map an O*NET-SOC code such as 15-2051.00 to six-digit SOC 152051."""
    return str(value).split(".", maxsplit=1)[0].replace("-", "").zfill(6)


def formatted_soc(value: str) -> str:
    compact = normalize_soc(value)
    return f"{compact[:2]}-{compact[2:]}"


def load_software_skills(directory: Path) -> pd.DataFrame:
    candidates = ("Software Skills.xlsx", "Technology Skills.xlsx")
    path = next(
        (_find(directory, name) for name in candidates if list(directory.rglob(name))),
        None,
    )
    if path is None:
        raise FileNotFoundError(f"No software/technology skills workbook below {directory}")

    frame = pd.read_excel(path)
    example_column = "Workplace Example" if "Workplace Example" in frame else "Example"
    normalized = frame.rename(
        columns={
            "O*NET-SOC Code": "onet_soc",
            "Title": "occupation_title",
            example_column: "skill",
            "Hot Technology": "hot",
            "In Demand": "in_demand",
        }
    )[["onet_soc", "occupation_title", "skill", "hot", "in_demand"]]
    normalized["soc_code"] = normalized["onet_soc"].map(normalize_soc)
    normalized["hot"] = normalized["hot"].eq("Y")
    normalized["in_demand"] = normalized["in_demand"].eq("Y")
    return normalized.dropna(subset=["skill"]).drop_duplicates()


def build_occupation_metrics(
    directory: Path,
    release: str,
    classifier: TransparentSkillClassifier | None = None,
) -> pd.DataFrame:
    classifier = classifier or TransparentSkillClassifier()
    skills = load_software_skills(directory)
    predictions = {
        skill: classifier.predict_one(str(skill))
        for skill in sorted(skills["skill"].astype(str).unique())
    }
    skills["category"] = skills["skill"].map(lambda value: predictions[str(value)].label)
    skills["confidence"] = skills["skill"].map(lambda value: predictions[str(value)].confidence)
    skills["classification_method"] = skills["skill"].map(
        lambda value: predictions[str(value)].method
    )
    skills["taxonomy_weight"] = skills["category"].map(taxonomy_weight)
    skills["demand_weight"] = (
        1.0 + (0.25 * skills["hot"].astype(float)) + (0.5 * skills["in_demand"].astype(float))
    )
    skills["ai_weighted_signal"] = skills["taxonomy_weight"] * skills["demand_weight"]
    skills["is_ai_related"] = skills["category"].ne(NON_AI_LABEL)
    skills["is_core_signal"] = skills["category"].eq("core_ai_ml")

    grouped = skills.groupby("soc_code", as_index=False).agg(
        occupation_title=("occupation_title", "first"),
        total_software_skills=("skill", "nunique"),
        ai_related_skills=("is_ai_related", "sum"),
        signal_numerator=("ai_weighted_signal", "sum"),
        signal_denominator=("demand_weight", "sum"),
        hot_skills=("hot", "sum"),
        in_demand_skills=("in_demand", "sum"),
        core_ai_skills=("is_core_signal", "sum"),
    )
    grouped["ai_intensity"] = (
        100.0 * grouped["signal_numerator"] / grouped["signal_denominator"]
    ).round(2)
    grouped.loc[grouped["core_ai_skills"].eq(0), "ai_intensity"] = 0.0
    grouped["ai_skill_share"] = (
        100.0 * grouped["ai_related_skills"] / grouped["total_software_skills"]
    ).round(2)
    grouped["release"] = release
    signal_sources = (
        skills[skills["is_core_signal"]]
        .groupby("soc_code")["occupation_title"]
        .agg(lambda values: "; ".join(sorted(set(values))))
        .rename("signal_occupation_titles")
        .reset_index()
    )
    grouped = grouped.merge(signal_sources, on="soc_code", how="left")
    grouped["signal_occupation_titles"] = grouped["signal_occupation_titles"].fillna("")

    category_counts = (
        skills[skills["category"].ne(NON_AI_LABEL)]
        .pivot_table(
            index="soc_code",
            columns="category",
            values="skill",
            aggfunc="nunique",
            fill_value=0,
        )
        .add_prefix("skills_")
        .reset_index()
    )
    return grouped.merge(category_counts, on="soc_code", how="left").fillna(0)


def load_education(directory: Path) -> pd.DataFrame:
    frame = pd.read_excel(_find(directory, "Education.xlsx"))
    frame = frame.rename(
        columns={
            "O*NET-SOC Code": "onet_soc",
            "Category": "category",
            "Data Value": "percent",
        }
    )
    frame["soc_code"] = frame["onet_soc"].map(normalize_soc)
    frame["percent"] = pd.to_numeric(frame["percent"], errors="coerce").fillna(0.0)
    frame["bachelors_plus"] = np.where(frame["category"] >= 6, frame["percent"], 0.0)
    return (
        frame.groupby("soc_code", as_index=False)
        .agg(bachelors_plus_share=("bachelors_plus", "sum"))
        .assign(bachelors_plus_share=lambda value: value["bachelors_plus_share"].clip(0, 100))
    )


def load_job_zones(directory: Path) -> pd.DataFrame:
    frame = pd.read_excel(_find(directory, "Job Zones.xlsx"))
    frame = frame.rename(columns={"O*NET-SOC Code": "onet_soc", "Job Zone": "job_zone"})
    frame["soc_code"] = frame["onet_soc"].map(normalize_soc)
    return frame.groupby("soc_code", as_index=False).agg(job_zone=("job_zone", "median"))


def build_task_complements(directory: Path, current_metrics: pd.DataFrame) -> pd.DataFrame:
    tasks = pd.read_excel(_find(directory, "Task Statements.xlsx"))
    tasks = tasks.rename(
        columns={
            "O*NET-SOC Code": "onet_soc",
            "Task": "task",
            "Task Type": "task_type",
        }
    )
    tasks = tasks[tasks["task_type"].eq("Core")].copy()
    tasks["soc_code"] = tasks["onet_soc"].map(normalize_soc)
    tasks["task_category"] = tasks["task"].map(classify_task)
    high_ai_count = max(1, int(np.ceil(len(current_metrics) * 0.25)))
    high_ai_socs = set(
        current_metrics.nlargest(high_ai_count, "ai_intensity")["soc_code"]
    )
    tasks = tasks.merge(
        current_metrics[["soc_code", "ai_intensity"]], on="soc_code", how="inner"
    )
    tasks["group"] = np.where(tasks["soc_code"].isin(high_ai_socs), "high_ai", "comparison")

    counts = (
        tasks.groupby(["group", "task_category"], as_index=False)
        .size()
        .rename(columns={"size": "tasks"})
    )
    counts["share"] = counts["tasks"] / counts.groupby("group")["tasks"].transform("sum")
    pivot = counts.pivot(index="task_category", columns="group", values="share").fillna(0)
    pivot["lift"] = np.where(
        pivot.get("comparison", 0) > 0,
        pivot.get("high_ai", 0) / pivot.get("comparison", 1),
        np.nan,
    )
    return (
        pivot.reset_index()
        .rename(columns={"high_ai": "high_ai_share", "comparison": "comparison_share"})
        .sort_values("lift", ascending=False)
    )
