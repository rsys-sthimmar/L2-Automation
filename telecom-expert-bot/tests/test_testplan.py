import pytest
from unittest.mock import AsyncMock

from app.services.testplan_generator import TestPlanGenerator
from app.utils.reference_mapper import map_to_spec_reference, get_spec_sections, get_all_specs


@pytest.mark.asyncio
async def test_generate_test_plan_no_llm():
    generator = TestPlanGenerator()
    result = await generator.generate(
        feature="RRC Connection Setup",
        domain="RRC",
        requirements=["UE must complete setup within 1 second"],
        llm_service=None,
    )
    assert "objective" in result
    assert "preconditions" in result
    assert "steps" in result
    assert "expected_results" in result
    assert "negative_scenarios" in result
    assert "kpis" in result
    assert "references" in result
    assert len(result["steps"]) > 0
    assert len(result["negative_scenarios"]) > 0
    assert "TS 38.331" in result["references"][0]


@pytest.mark.asyncio
async def test_generate_test_plan_with_mock_llm():
    generator = TestPlanGenerator()
    mock_llm = type("MockLLM", (), {
        "generate_test_plan": AsyncMock(return_value=(
            "Objective: Test NGSetup procedure\n"
            "Preconditions:\n- gNB available\n- AMF running\n"
            "Steps:\n- Trigger NG Setup\n- Verify response\n"
            "Expected Results:\n- Setup success\n"
            "KPIs:\n- Success rate > 99%\n"
        ))
    })()
    result = await generator.generate(
        feature="NG Setup",
        domain="NGAP",
        llm_service=mock_llm,
    )
    assert "objective" in result
    assert "steps" in result
    assert len(result["steps"]) >= 0


@pytest.mark.asyncio
async def test_generate_test_plan_different_domains():
    generator = TestPlanGenerator()
    for domain, expected_spec in [("RRC", "TS 38.331"), ("NGAP", "TS 38.413"), ("F1AP", "TS 38.473")]:
        result = await generator.generate(
            feature=f"{domain} Test",
            domain=domain,
            llm_service=None,
        )
        assert expected_spec in result["references"][0]


def test_reference_mapper():
    rrc_ref = map_to_spec_reference("RRC")
    assert rrc_ref["spec"] == "TS 38.331"

    ngap_ref = map_to_spec_reference("NGAP")
    assert ngap_ref["spec"] == "TS 38.413"

    ntn_ref = map_to_spec_reference("NTN")
    assert ntn_ref["spec"] == "TS 38.821"


def test_get_spec_sections():
    sections = get_spec_sections("TS 38.331")
    assert len(sections) > 0

    sections = get_spec_sections("TS 38.413")
    assert len(sections) > 0


def test_get_all_specs():
    specs = get_all_specs()
    assert "RRC" in specs
    assert "NGAP" in specs
    assert "F1AP" in specs
    assert "NTN" in specs
    assert specs["RRC"] == "TS 38.331"
