from __future__ import annotations

import re
from collections.abc import Iterable

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from .models import SkillPrediction

TAXONOMY: dict[str, dict[str, object]] = {
    "core_ai_ml": {
        "description": "Model development, machine learning, NLP, vision, and generative AI.",
        "weight": 1.0,
        "terms": (
            "artificial intelligence",
            "machine learning",
            "deep learning",
            "neural network",
            "natural language processing",
            "computer vision",
            "large language model",
            "generative ai",
            "pytorch",
            "tensorflow",
            "keras",
            "scikit-learn",
            "xgboost",
            "transformers",
            "opencv",
            "hugging face",
        ),
    },
    "mlops_cloud": {
        "description": "Model deployment, orchestration, cloud ML, and reproducibility.",
        "weight": 0.65,
        "terms": (
            "mlflow",
            "kubeflow",
            "sagemaker",
            "vertex ai",
            "azure machine learning",
            "docker",
            "kubernetes",
            "airflow",
            "model monitoring",
            "feature store",
        ),
    },
    "data_engineering": {
        "description": "Data pipelines and platforms that make AI systems possible.",
        "weight": 0.4,
        "terms": (
            "apache spark",
            "hadoop",
            "kafka",
            "snowflake",
            "databricks",
            "data warehouse",
            "data pipeline",
            "extract transform load",
            "dbt",
            "sql",
        ),
    },
    "analytics": {
        "description": "Statistical computing, business intelligence, and quantitative analysis.",
        "weight": 0.25,
        "terms": (
            "python",
            "r software",
            "sas",
            "matlab",
            "tableau",
            "power bi",
            "statistical",
            "econometric",
            "data visualization",
        ),
    },
}

NON_AI_LABEL = "other"

_SEED_EXAMPLES: tuple[tuple[str, str], ...] = (
    ("PyTorch neural network training", "core_ai_ml"),
    ("TensorFlow deep learning models", "core_ai_ml"),
    ("natural language processing transformers", "core_ai_ml"),
    ("computer vision and OpenCV", "core_ai_ml"),
    ("large language model fine tuning", "core_ai_ml"),
    ("Kubernetes model serving", "mlops_cloud"),
    ("MLflow experiment tracking", "mlops_cloud"),
    ("SageMaker deployment", "mlops_cloud"),
    ("Airflow feature pipeline", "mlops_cloud"),
    ("Docker model monitoring", "mlops_cloud"),
    ("Apache Spark data processing", "data_engineering"),
    ("SQL data warehouse", "data_engineering"),
    ("Kafka streaming platform", "data_engineering"),
    ("Snowflake ETL pipeline", "data_engineering"),
    ("Databricks lakehouse", "data_engineering"),
    ("Python statistical analysis", "analytics"),
    ("R statistical software", "analytics"),
    ("SAS econometric analysis", "analytics"),
    ("Tableau dashboard", "analytics"),
    ("Power BI visualization", "analytics"),
    ("Adobe Acrobat document software", NON_AI_LABEL),
    ("Microsoft Word word processing", NON_AI_LABEL),
    ("AutoCAD design software", NON_AI_LABEL),
    ("QuickBooks accounting software", NON_AI_LABEL),
    ("JIRA project management", NON_AI_LABEL),
    ("Salesforce customer relationship management", NON_AI_LABEL),
)


def normalize_skill(text: str) -> str:
    cleaned = re.sub(r"[^a-z0-9+#.-]+", " ", str(text).lower())
    return re.sub(r"\s+", " ", cleaned).strip()


class TransparentSkillClassifier:
    """Lexicon-first classifier with an inspectable linear fallback.

    Exact taxonomy matches take priority. Unmatched text is classified by a
    deterministic TF-IDF logistic-regression model trained on public seed
    phrases. Low-confidence predictions remain ``other``.
    """

    def __init__(self, threshold: float = 0.56) -> None:
        self.threshold = threshold
        self._pipeline = Pipeline(
            [
                (
                    "tfidf",
                    TfidfVectorizer(
                        ngram_range=(1, 2),
                        lowercase=True,
                        sublinear_tf=True,
                    ),
                ),
                (
                    "classifier",
                    LogisticRegression(
                        random_state=42,
                        max_iter=1_000,
                        class_weight="balanced",
                    ),
                ),
            ]
        )
        examples, labels = zip(*_SEED_EXAMPLES, strict=True)
        self._pipeline.fit(examples, labels)

    def predict_one(self, text: str) -> SkillPrediction:
        normalized = normalize_skill(text)
        direct_matches: list[tuple[str, str]] = []
        for label, config in TAXONOMY.items():
            for term in config["terms"]:
                normalized_term = normalize_skill(str(term))
                pattern = rf"(?<![a-z0-9]){re.escape(normalized_term)}(?![a-z0-9])"
                if re.search(pattern, normalized):
                    direct_matches.append((label, str(term)))

        if direct_matches:
            direct_matches.sort(
                key=lambda item: (
                    float(TAXONOMY[item[0]]["weight"]),
                    len(item[1]),
                ),
                reverse=True,
            )
            label = direct_matches[0][0]
            matched = tuple(term for candidate, term in direct_matches if candidate == label)
            return SkillPrediction(label, 1.0, "lexicon", matched)

        probabilities = self._pipeline.predict_proba([normalized])[0]
        classes = self._pipeline.classes_
        best_index = int(np.argmax(probabilities))
        label = str(classes[best_index])
        confidence = float(probabilities[best_index])
        if confidence < self.threshold:
            label = NON_AI_LABEL
        return SkillPrediction(label, round(confidence, 4), "linear_tfidf")

    def predict(self, texts: Iterable[str]) -> list[SkillPrediction]:
        return [self.predict_one(text) for text in texts]


def taxonomy_weight(label: str) -> float:
    if label == NON_AI_LABEL:
        return 0.0
    return float(TAXONOMY[label]["weight"])
