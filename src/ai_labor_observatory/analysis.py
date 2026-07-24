from __future__ import annotations

import math

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from .models import WageModelResult


def build_skill_trends(previous: pd.DataFrame, current: pd.DataFrame) -> pd.DataFrame:
    columns = ["soc_code", "occupation_title", "ai_intensity", "ai_skill_share"]
    left = previous[columns].rename(
        columns={
            "occupation_title": "previous_title",
            "ai_intensity": "previous_ai_intensity",
            "ai_skill_share": "previous_ai_skill_share",
        }
    )
    right = current[columns].rename(
        columns={
            "occupation_title": "occupation_title",
            "ai_intensity": "current_ai_intensity",
            "ai_skill_share": "current_ai_skill_share",
        }
    )
    trends = right.merge(left, on="soc_code", how="inner")
    trends["intensity_change"] = (
        trends["current_ai_intensity"] - trends["previous_ai_intensity"]
    ).round(2)
    trends["skill_share_change"] = (
        trends["current_ai_skill_share"] - trends["previous_ai_skill_share"]
    ).round(2)
    return trends.sort_values(
        ["intensity_change", "current_ai_intensity"], ascending=[False, False]
    )


def fit_wage_model(frame: pd.DataFrame) -> WageModelResult:
    model_data = frame.dropna(
        subset=["annual_median_wage", "ai_intensity", "bachelors_plus_share", "job_zone"]
    ).copy()
    model_data = model_data[model_data["annual_median_wage"] > 0]
    model_data["major_group"] = model_data["soc_code"].str[:2]
    if len(model_data) < 30:
        raise ValueError("At least 30 complete occupations are required for the wage model")

    model = smf.ols(
        "np.log(annual_median_wage) ~ ai_intensity + bachelors_plus_share "
        "+ job_zone + C(major_group)",
        data=model_data,
    ).fit(cov_type="HC3")
    coefficient = float(model.params["ai_intensity"])
    ten_point_effect = math.expm1(coefficient * 10) * 100
    return WageModelResult(
        observations=int(model.nobs),
        coefficient=coefficient,
        standard_error=float(model.bse["ai_intensity"]),
        p_value=float(model.pvalues["ai_intensity"]),
        r_squared=float(model.rsquared),
        interpretation=(
            f"A 10-point higher AI-intensity score is associated with "
            f"{ten_point_effect:.1f}% different median annual wages, conditional on "
            "bachelor's-plus share, job zone, and major occupation group. "
            "This is a descriptive association, not a causal estimate."
        ),
    )


def summarize_geography(
    geography: pd.DataFrame, national: pd.DataFrame
) -> pd.DataFrame:
    national_wages = national[["soc_code", "annual_median_wage"]].rename(
        columns={"annual_median_wage": "national_median_wage"}
    )
    result = geography.merge(national_wages, on="soc_code", how="left")
    result["wage_index"] = (
        100 * result["annual_median_wage"] / result["national_median_wage"]
    ).replace([np.inf, -np.inf], np.nan)
    return result.sort_values(["area_name", "wage_index"], ascending=[True, False])
