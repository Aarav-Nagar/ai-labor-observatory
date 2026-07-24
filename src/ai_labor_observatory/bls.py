from __future__ import annotations

import time
from collections.abc import Iterable, Sequence

import httpx
import pandas as pd

from .models import BlsObservation

BLS_API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

STATE_AREAS: dict[str, str] = {
    "0600000": "California",
    "1200000": "Florida",
    "1700000": "Illinois",
    "2500000": "Massachusetts",
    "3600000": "New York",
    "3700000": "North Carolina",
    "4800000": "Texas",
    "5100000": "Virginia",
    "5300000": "Washington",
}

DATATYPES = {
    "employment": "01",
    "annual_median_wage": "13",
}


def build_series_id(soc_code: str, datatype: str, area_code: str = "0000000") -> str:
    compact_soc = str(soc_code).replace("-", "")
    area_type = "N" if area_code == "0000000" else "S"
    series_id = f"OEU{area_type}{area_code}000000{compact_soc}{DATATYPES[datatype]}"
    if len(series_id) != 25:
        raise ValueError(f"Invalid OEWS series ID components produced {series_id!r}")
    return series_id


def _chunks(values: Sequence[str], size: int) -> Iterable[Sequence[str]]:
    for start in range(0, len(values), size):
        yield values[start : start + size]


class BlsClient:
    def __init__(
        self,
        registration_key: str | None = None,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.registration_key = registration_key
        self.client = httpx.Client(timeout=timeout, transport=transport)

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> BlsClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def fetch(
        self,
        soc_codes: Sequence[str],
        year: int,
        areas: dict[str, str] | None = None,
    ) -> pd.DataFrame:
        areas = areas or {"0000000": "United States"}
        requested: dict[str, tuple[str, str, str, str]] = {}
        for area_code, area_name in areas.items():
            for soc_code in soc_codes:
                for metric in DATATYPES:
                    series_id = build_series_id(soc_code, metric, area_code)
                    requested[series_id] = (soc_code, area_code, area_name, metric)

        values: dict[tuple[str, str], dict[str, float | None]] = {}
        series_ids = sorted(requested)
        batch_size = 50 if self.registration_key else 25
        for batch_number, batch in enumerate(_chunks(series_ids, batch_size)):
            payload: dict[str, object] = {
                "seriesid": list(batch),
                "startyear": str(year),
                "endyear": str(year),
            }
            if self.registration_key:
                payload["registrationkey"] = self.registration_key
            response = self.client.post(BLS_API_URL, json=payload)
            response.raise_for_status()
            body = response.json()
            if body.get("status") != "REQUEST_SUCCEEDED":
                raise RuntimeError(f"BLS request failed: {body.get('message')}")
            for series in body["Results"]["series"]:
                series_id = series["seriesID"]
                soc_code, area_code, _, metric = requested[series_id]
                key = (soc_code, area_code)
                values.setdefault(key, {"employment": None, "annual_median_wage": None})
                observations = [
                    item
                    for item in series.get("data", [])
                    if item.get("year") == str(year) and item.get("period") == "A01"
                ]
                if observations:
                    try:
                        values[key][metric] = float(observations[0]["value"])
                    except (TypeError, ValueError):
                        values[key][metric] = None
            if batch_number and batch_number % 10 == 0:
                time.sleep(0.2)

        rows: list[BlsObservation] = []
        for (soc_code, area_code), metrics in values.items():
            rows.append(
                BlsObservation(
                    soc_code=soc_code,
                    area_code=area_code,
                    area_name=areas[area_code],
                    year=year,
                    employment=metrics["employment"],
                    annual_median_wage=metrics["annual_median_wage"],
                )
            )
        return pd.DataFrame([row.as_dict() for row in rows])
