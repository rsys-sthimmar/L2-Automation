import pytest
from unittest.mock import AsyncMock

from app.services.log_analyzer import LogAnalyzer
from app.utils.protocol_decoder import decode_message, decode_log, RRCDecoder, NGAPDecoder, F1APDecoder


SAMPLE_RRC_LOG = """
2024-01-01 10:00:00 [INFO] RRCSetupRequest received from UE rnti=1234
2024-01-01 10:00:01 [INFO] RRCSetup sent to UE rnti=1234
2024-01-01 10:00:02 [INFO] RRCSetupComplete received from UE rnti=1234
"""

SAMPLE_NGAP_LOG = """
2024-01-01 10:00:00 [INFO] NGSetupRequest received from gNB
2024-01-01 10:00:01 [INFO] NGSetupResponse sent to gNB
2024-01-01 10:00:05 [INFO] InitialUEMessage received ue_id=1
2024-01-01 10:00:06 [ERROR] InitialContextSetupRequest failed cause=timeout
"""

SAMPLE_F1AP_LOG = """
2024-01-01 10:00:00 [INFO] F1SetupRequest received from DU
2024-01-01 10:00:01 [INFO] F1SetupResponse sent to DU
"""


def test_decode_rrc_message():
    result = decode_message("RRCSetup sent to UE rnti=1234")
    assert result is not None
    assert result["message_name"] == "RRCSetup"
    assert result["domain"] == "RRC"
    assert "TS 38.331" in result["spec_reference"]


def test_decode_ngap_message():
    result = decode_message("InitialUEMessage received ue_id=1")
    assert result is not None
    assert result["message_name"] == "InitialUEMessage"
    assert result["domain"] == "NGAP"
    assert "TS 38.413" in result["spec_reference"]


def test_decode_f1ap_message():
    result = decode_message("F1SetupRequest received from DU")
    assert result is not None
    assert result["message_name"] == "F1SetupRequest"
    assert result["domain"] == "F1AP"
    assert "TS 38.473" in result["spec_reference"]


def test_decode_unknown_message():
    result = decode_message("Some random log line with no known message")
    assert result is None


def test_decode_full_log():
    decoded = decode_log(SAMPLE_RRC_LOG)
    assert len(decoded) >= 3
    message_names = [d["message_name"] for d in decoded]
    assert "RRCSetupRequest" in message_names
    assert "RRCSetup" in message_names
    assert "RRCSetupComplete" in message_names


def test_rrc_decoder():
    decoder = RRCDecoder()
    result = decoder.decode("RRCReconfiguration sent to UE")
    assert result is not None
    assert result["domain"] == "RRC"


def test_ngap_decoder():
    decoder = NGAPDecoder()
    result = decoder.decode("NGSetupRequest received")
    assert result is not None
    assert result["domain"] == "NGAP"


def test_f1ap_decoder():
    decoder = F1APDecoder()
    result = decoder.decode("F1SetupResponse sent")
    assert result is not None
    assert result["domain"] == "F1AP"


@pytest.mark.asyncio
async def test_log_analyzer_without_llm():
    analyzer = LogAnalyzer()
    result = await analyzer.analyze(SAMPLE_NGAP_LOG, llm_service=None)
    assert "decoded_messages" in result
    assert "failures" in result
    assert "procedure_map" in result
    assert "root_cause" in result
    assert "suggestions" in result
    assert "confidence" in result
    assert len(result["decoded_messages"]) > 0
    assert len(result["failures"]) > 0


@pytest.mark.asyncio
async def test_log_analyzer_with_mock_llm():
    analyzer = LogAnalyzer()
    mock_llm = type("MockLLM", (), {
        "analyze_logs": AsyncMock(return_value="Root Cause: Timeout detected.\nSuggestions:\n- Check timer values")
    })()
    result = await analyzer.analyze(SAMPLE_NGAP_LOG, llm_service=mock_llm)
    assert result["raw_analysis"] is not None
    assert "decoded_messages" in result


@pytest.mark.asyncio
async def test_log_analyzer_no_failures():
    analyzer = LogAnalyzer()
    clean_log = """
2024-01-01 10:00:00 [INFO] RRCSetup sent to UE
2024-01-01 10:00:01 [INFO] RRCSetupComplete received
"""
    result = await analyzer.analyze(clean_log, llm_service=None)
    assert result["decoded_messages"] is not None
    assert isinstance(result["suggestions"], list)
