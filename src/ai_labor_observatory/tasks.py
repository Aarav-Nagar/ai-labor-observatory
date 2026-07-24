from __future__ import annotations

import re
from collections import Counter

TASK_TAXONOMY: dict[str, tuple[str, ...]] = {
    "analytical_judgment": (
        "analy",
        "evaluate",
        "assess",
        "interpret",
        "forecast",
        "diagnos",
        "decide",
        "strategy",
        "research",
    ),
    "interpersonal": (
        "communicat",
        "confer",
        "advise",
        "negotiate",
        "teach",
        "interview",
        "coordinate",
        "supervise",
        "assist",
    ),
    "creative_communication": (
        "design",
        "develop",
        "write",
        "present",
        "create",
        "compose",
        "plan",
    ),
    "technical_computational": (
        "program",
        "software",
        "database",
        "model",
        "algorithm",
        "computer",
        "code",
        "simulate",
    ),
    "routine_information": (
        "record",
        "file",
        "enter data",
        "verify",
        "schedule",
        "process forms",
        "compile",
        "calculate",
    ),
    "physical_operational": (
        "operate",
        "repair",
        "install",
        "lift",
        "clean",
        "inspect equipment",
        "drive",
        "assemble",
        "measure",
    ),
}


def classify_task(text: str) -> str:
    normalized = re.sub(r"\s+", " ", str(text).lower())
    scores = Counter(
        {
            label: sum(1 for term in terms if term in normalized)
            for label, terms in TASK_TAXONOMY.items()
        }
    )
    label, score = scores.most_common(1)[0]
    return label if score > 0 else "other"
