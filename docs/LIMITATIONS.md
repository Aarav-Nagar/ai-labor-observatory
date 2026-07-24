# Limitations

## Coverage

O*NET software-skill indicators are based on employer job postings but are not a census
of every U.S. vacancy. Collection, vendor coverage, occupation mapping, and publication
thresholds may affect the observed signal.

## Version comparability

O*NET 30.3 modernized parts of the content model, including the transition from
Technology Skills to Software Skills. The pipeline normalizes the common fields, but a
release-to-release change can reflect both labor demand and methodology changes.

## Classifier

The hybrid classifier prioritizes auditability over frontier accuracy. The seed set is
small, categories overlap, software names are ambiguous, and the weights are analytical
choices. Thresholds and predictions should be sensitivity-tested before policy use.

## Wage analysis

The regression is cross-sectional and occupation-level. It cannot separate:

- worker selection
- industry composition
- firm size
- location and cost of living beyond the displayed state comparison
- experience and seniority
- unobserved occupational complexity

The reported coefficient must not be interpreted as a causal wage premium.

## Tasks

The task taxonomy is a deterministic text mapping. Lift measures relative task shares,
not whether AI complements, substitutes for, or automates a particular worker.

## BLS observations

OEWS excludes self-employed workers and publishes estimates with sampling error.
Suppressed values are kept missing. The committed snapshot is a release-specific
research artifact, not a live compensation quote.

## Geographic analysis

Nine selected states provide a readable comparison, not complete national geography.
State wage differences are not cost-of-living adjusted.
