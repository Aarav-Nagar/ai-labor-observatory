# Analytical Snapshot

Generated from:

- O*NET 29.3 (May 2025)
- O*NET 30.3 (May 2026)
- BLS OEWS May 2025 annual estimates

Files:

- `occupation_metrics.csv` — AI intensity, education, job zone, employment, and wages
- `skill_trends.csv` — comparable release-to-release occupation signals
- `task_complements.csv` — task-family shares and lift
- `geography.csv` — state wage indices and employment
- `bls_national.csv` / `bls_geography.csv` — network cache for reproducible offline builds
- `summary.json` — bounded dashboard/API snapshot

The final offline rebuild reports three newly selected occupation codes absent from the
BLS cache after the public API’s daily quota was reached. They are excluded from the
wage model rather than imputed. The summary records this boundary.

O*NET data attribution and license details are in
[`docs/DATA_SOURCES.md`](../../docs/DATA_SOURCES.md).
