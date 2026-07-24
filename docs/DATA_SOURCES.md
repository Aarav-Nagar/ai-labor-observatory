# Data Sources and Licensing

## O*NET database

This project uses the downloadable:

- O*NET 29.3 Database, May 2025
- O*NET 30.3 Database, May 2026

Source: <https://www.onetcenter.org/database.html>

The O*NET database is licensed under the
[Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/).

Required attribution:

> This project includes information from the O*NET 30.3 Database by the U.S.
> Department of Labor, Employment and Training Administration (USDOL/ETA), used under
> the CC BY 4.0 license. AI Labor Observatory has modified and aggregated portions of
> this information. USDOL/ETA has not approved, endorsed, or tested these modifications.
> O*NET® is a trademark of USDOL/ETA.

The `Technology Skills.xlsx` and `Software Skills.xlsx` files include hot and in-demand
designations derived by O*NET from employer job postings. This repository redistributes
only transformed, attributed aggregate features—not a proprietary raw posting corpus.

## Bureau of Labor Statistics

The project queries the BLS Occupational Employment and Wage Statistics public API:

- API documentation: <https://www.bls.gov/developers/>
- OEWS program: <https://www.bls.gov/oes/>
- series mapping documentation: <https://download.bls.gov/pub/time.series/oe/oe.txt>

The analytical snapshot uses May 2025 annual employment and median wage observations,
released in 2026. Suppressed observations remain missing.

## USAJOBS decision

USAJOBS offers public API endpoints, but its API terms restrict reuse and derivative
redistribution. This repository therefore does not commit USAJOBS announcement text or
derived announcement-level data. The legally cleaner O*NET CC BY job-posting-derived
signals provide the demand input.

This is an engineering data-governance decision, not legal advice.

## Snapshot provenance

`data/sample/summary.json` records source releases and generation time. Raw archives are
excluded from version control and can be re-downloaded with:

```bash
labor-observatory fetch-sources --destination data/raw
```
