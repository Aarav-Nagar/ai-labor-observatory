# Methodology

## Research unit

The primary unit is a six-digit 2018 Standard Occupational Classification (SOC)
occupation. O*NET detailed occupations such as `15-2051.01` are aggregated to their
six-digit parent (`15-2051`) before joining BLS OEWS observations.

## Software-skill taxonomy

The classifier is intentionally inspectable:

1. Normalize punctuation and whitespace.
2. Apply high-precision taxonomy phrases.
3. For unmatched text, apply a TF-IDF unigram/bigram logistic-regression classifier.
4. Leave predictions below 0.56 confidence in `other`.
5. Retain label, confidence, method, and matched phrases.

The categories and weights live in `taxonomy.py`; there is no remote model, hidden
prompt, or paid API.

## AI intensity

The score is a weighted share, not a probability:

```text
demand_weight = 1 + 0.25(hot) + 0.50(in_demand)
weighted_signal = taxonomy_weight × demand_weight
AI intensity = 100 × sum(weighted_signal) / sum(demand_weight)
```

The denominator includes all software skills linked to an occupation. This prevents an
occupation with a single generic AI-adjacent term from automatically ranking above an
occupation with broad, explicit AI demand.

An occupation must also contain at least one core-AI/ML skill. MLOps, data engineering,
or analytics skills without that gate are treated as general digital readiness rather
than AI intensity.

## Change over time

The release comparison inner-joins occupations present in both O*NET 29.3 (May 2025)
and O*NET 30.3 (May 2026). The displayed change is:

```text
current AI intensity − previous AI intensity
```

This is a release-to-release signal. It is not a continuous monthly job-posting index.

## Wage model

The cross-sectional model is:

```text
log(median annual wage) =
  β₀ + β₁(AI intensity)
     + β₂(bachelor's-plus share)
     + β₃(job zone)
     + major SOC fixed effects
     + ε
```

It uses HC3 heteroskedasticity-robust standard errors. The model is descriptive.
Occupation-level skill composition, education, and wages do not identify an individual
worker’s causal return to AI skills.

## Task complementarity

Core O*NET task statements are assigned to an inspectable keyword taxonomy:

- analytical judgment
- interpersonal
- creative communication
- technical computational
- routine information
- physical operational
- other

For each task family, lift is:

```text
share among top-quartile AI-intensity occupations
--------------------------------------------------
share among all remaining occupations
```

Lift describes co-occurrence. It does not measure automation probability,
substitutability, or future job loss.

## Geography

The dashboard compares selected, recognizable AI-intensive occupations across nine
states. The wage index is:

```text
100 × state median annual wage / national median annual wage
```

Missing and suppressed values are not imputed.
