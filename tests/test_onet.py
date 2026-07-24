from ai_labor_observatory.onet import formatted_soc, normalize_soc
from ai_labor_observatory.tasks import classify_task


def test_soc_normalization_removes_onet_detail_suffix() -> None:
    assert normalize_soc("15-2051.01") == "152051"
    assert formatted_soc("152051") == "15-2051"


def test_task_taxonomy_surfaces_analytical_complements() -> None:
    assert (
        classify_task("Analyze economic data to evaluate policy alternatives.")
        == "analytical_judgment"
    )
    assert classify_task("Install and repair industrial equipment.") == "physical_operational"
