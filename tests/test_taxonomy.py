from ai_labor_observatory.taxonomy import (
    NON_AI_LABEL,
    TransparentSkillClassifier,
    normalize_skill,
    taxonomy_weight,
)


def test_lexicon_classifies_core_ai_skill_with_evidence() -> None:
    prediction = TransparentSkillClassifier().predict_one("PyTorch neural network software")

    assert prediction.label == "core_ai_ml"
    assert prediction.method == "lexicon"
    assert "pytorch" in prediction.matched_terms
    assert prediction.confidence == 1.0


def test_non_ai_office_software_remains_outside_ai_taxonomy() -> None:
    prediction = TransparentSkillClassifier().predict_one("Microsoft Word")

    assert prediction.label == NON_AI_LABEL
    assert taxonomy_weight(prediction.label) == 0


def test_phrase_boundaries_do_not_treat_browser_as_r_software() -> None:
    prediction = TransparentSkillClassifier().predict_one("Web browser software")

    assert prediction.label == NON_AI_LABEL


def test_normalization_is_stable() -> None:
    assert normalize_skill("  Scikit-Learn / Python  ") == "scikit-learn python"
