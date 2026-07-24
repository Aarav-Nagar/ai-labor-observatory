from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class SkillPrediction:
    label: str
    confidence: float
    method: str
    matched_terms: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BlsObservation:
    soc_code: str
    area_code: str
    area_name: str
    year: int
    employment: float | None
    annual_median_wage: float | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WageModelResult:
    observations: int
    coefficient: float
    standard_error: float
    p_value: float
    r_squared: float
    interpretation: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
