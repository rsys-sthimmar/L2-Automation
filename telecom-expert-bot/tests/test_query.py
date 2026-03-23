import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_health_endpoint(async_client):
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_query_requires_auth(async_client):
    response = await async_client.post("/query", json={"question": "What is RRCSetup?"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_query_with_auth(async_client, master_user_token):
    mock_result = {
        "answer": "RRCSetup is defined in TS 38.331 Section 6.2.2.",
        "references": ["TS 38.331 Section 6.2.2"],
        "confidence": "high",
        "domain": "RRC",
        "message_flow": None,
        "edge_cases": None,
    }
    with patch("app.routers.query.llm_service") as mock_llm, \
         patch("app.routers.query.spec_retriever") as mock_retriever:
        mock_llm.query = AsyncMock(return_value=mock_result)
        mock_retriever.get_context_for_query = AsyncMock(return_value="")

        response = await async_client.post(
            "/query",
            json={"question": "What is RRCSetup?"},
            headers={"Authorization": f"Bearer {master_user_token}"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert "answer" in body["data"]


@pytest.mark.asyncio
async def test_query_with_domain(async_client, child_user_token):
    mock_result = {
        "answer": "NGAP is defined in TS 38.413.",
        "references": ["TS 38.413"],
        "confidence": "high",
        "domain": "NGAP",
        "message_flow": None,
        "edge_cases": None,
    }
    with patch("app.routers.query.llm_service") as mock_llm, \
         patch("app.routers.query.spec_retriever") as mock_retriever:
        mock_llm.query = AsyncMock(return_value=mock_result)
        mock_retriever.get_context_for_query = AsyncMock(return_value="")

        response = await async_client.post(
            "/query",
            json={"question": "Explain InitialUEMessage", "domain": "NGAP"},
            headers={"Authorization": f"Bearer {child_user_token}"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["domain"] == "NGAP"


@pytest.mark.asyncio
async def test_domain_detection():
    from app.utils.reference_mapper import detect_domain_from_query
    assert detect_domain_from_query("What is RRCSetup procedure?") == "RRC"
    assert detect_domain_from_query("Explain NGAP InitialUEMessage") == "NGAP"
    assert detect_domain_from_query("How does NTN work with satellite?") == "NTN"
    assert detect_domain_from_query("Describe F1AP setup") == "F1AP"
