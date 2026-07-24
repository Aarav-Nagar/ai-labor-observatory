import numpy as np
import pandas as pd

from ai_labor_observatory.analysis import build_skill_trends, fit_wage_model


def test_skill_trends_are_sorted_by_change() -> None:
    previous = pd.DataFrame(
        {
            "soc_code": ["111111", "222222"],
            "occupation_title": ["A", "B"],
            "ai_intensity": [5.0, 2.0],
            "ai_skill_share": [5.0, 2.0],
        }
    )
    current = pd.DataFrame(
        {
            "soc_code": ["111111", "222222"],
            "occupation_title": ["A", "B"],
            "ai_intensity": [6.0, 7.0],
            "ai_skill_share": [6.0, 7.0],
        }
    )

    result = build_skill_trends(previous, current)

    assert result.iloc[0]["soc_code"] == "222222"
    assert result.iloc[0]["intensity_change"] == 5.0


def test_wage_model_returns_explicit_noncausal_interpretation() -> None:
    rng = np.random.default_rng(42)
    rows = []
    for index in range(80):
        intensity = float(index % 25)
        education = float(30 + (index % 50))
        wage = float(np.exp(10.6 + 0.008 * intensity + rng.normal(0, 0.08)))
        rows.append(
            {
                "soc_code": f"{11 + (index % 8):02d}{index % 10_000:04d}",
                "annual_median_wage": wage,
                "ai_intensity": intensity,
                "bachelors_plus_share": education,
                "job_zone": 2 + (index % 4),
            }
        )

    result = fit_wage_model(pd.DataFrame(rows))

    assert result.observations == 80
    assert 0 <= result.r_squared <= 1
    assert "not a causal estimate" in result.interpretation
