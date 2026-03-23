import pytest
from unittest.mock import patch


@pytest.mark.asyncio
async def test_create_knowledge_as_master(async_client, master_user_token):
    response = await async_client.post(
        "/knowledge",
        json={
            "title": "RRC Setup Procedure",
            "content": "RRC Setup is initiated when...",
            "domain": "RRC",
            "feature": "connection_setup",
            "spec_references": ["TS 38.331 Section 6.2.2"],
        },
        headers={"Authorization": f"Bearer {master_user_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["state"] == "confirmed"


@pytest.mark.asyncio
async def test_create_knowledge_as_child(async_client, child_user_token):
    response = await async_client.post(
        "/knowledge",
        json={
            "title": "NGAP Setup",
            "content": "NGAP setup procedure involves...",
            "domain": "NGAP",
            "spec_references": [],
        },
        headers={"Authorization": f"Bearer {child_user_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["state"] == "pending"


@pytest.mark.asyncio
async def test_list_knowledge(async_client, master_user_token):
    response = await async_client.get(
        "/knowledge",
        headers={"Authorization": f"Bearer {master_user_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert isinstance(body["data"], list)


@pytest.mark.asyncio
async def test_approve_knowledge_as_master(async_client, master_user_token, child_user_token):
    create_resp = await async_client.post(
        "/knowledge",
        json={
            "title": "F1AP Setup",
            "content": "F1AP setup...",
            "domain": "F1AP",
            "spec_references": [],
        },
        headers={"Authorization": f"Bearer {child_user_token}"},
    )
    assert create_resp.status_code == 200
    item_id = create_resp.json()["data"]["id"]
    assert create_resp.json()["data"]["state"] == "pending"

    approve_resp = await async_client.post(
        f"/knowledge/{item_id}/approve",
        headers={"Authorization": f"Bearer {master_user_token}"},
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["data"]["state"] == "confirmed"


@pytest.mark.asyncio
async def test_reject_knowledge_as_master(async_client, master_user_token, child_user_token):
    create_resp = await async_client.post(
        "/knowledge",
        json={
            "title": "MAC Scheduling",
            "content": "MAC scheduling...",
            "domain": "MAC",
            "spec_references": [],
        },
        headers={"Authorization": f"Bearer {child_user_token}"},
    )
    item_id = create_resp.json()["data"]["id"]

    reject_resp = await async_client.post(
        f"/knowledge/{item_id}/reject",
        headers={"Authorization": f"Bearer {master_user_token}"},
    )
    assert reject_resp.status_code == 200
    assert reject_resp.json()["data"]["state"] == "rejected"


@pytest.mark.asyncio
async def test_child_cannot_delete(async_client, child_user_token, master_user_token):
    create_resp = await async_client.post(
        "/knowledge",
        json={"title": "Test", "content": "Test content", "domain": "RRC", "spec_references": []},
        headers={"Authorization": f"Bearer {master_user_token}"},
    )
    item_id = create_resp.json()["data"]["id"]

    delete_resp = await async_client.delete(
        f"/knowledge/{item_id}",
        headers={"Authorization": f"Bearer {child_user_token}"},
    )
    assert delete_resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_knowledge_as_master(async_client, master_user_token):
    create_resp = await async_client.post(
        "/knowledge",
        json={"title": "To Delete", "content": "Delete me", "domain": "RRC", "spec_references": []},
        headers={"Authorization": f"Bearer {master_user_token}"},
    )
    item_id = create_resp.json()["data"]["id"]

    delete_resp = await async_client.delete(
        f"/knowledge/{item_id}",
        headers={"Authorization": f"Bearer {master_user_token}"},
    )
    assert delete_resp.status_code == 200
    assert delete_resp.json()["status"] == "success"
