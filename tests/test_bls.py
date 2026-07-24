import httpx

from ai_labor_observatory.bls import BlsClient, build_series_id


def test_build_national_and_state_series_ids() -> None:
    assert build_series_id("15-2051", "annual_median_wage") == "OEUN000000000000015205113"
    assert (
        build_series_id("151252", "employment", "0600000")
        == "OEUS060000000000015125201"
    )


def test_client_preserves_missing_estimates() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = request.read().decode()
        assert "OEUN000000000000015205113" in body
        return httpx.Response(
            200,
            json={
                "status": "REQUEST_SUCCEEDED",
                "message": [],
                "Results": {
                    "series": [
                        {
                            "seriesID": "OEUN000000000000015205101",
                            "data": [
                                {
                                    "year": "2025",
                                    "period": "A01",
                                    "value": "245900",
                                }
                            ],
                        },
                        {
                            "seriesID": "OEUN000000000000015205113",
                            "data": [],
                        },
                    ]
                },
            },
        )

    transport = httpx.MockTransport(handler)
    with BlsClient(transport=transport) as client:
        frame = client.fetch(["152051"], 2025)

    assert frame.iloc[0]["employment"] == 245900
    assert frame.iloc[0]["annual_median_wage"] is None
