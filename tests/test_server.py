"""Tests for MCP server tool dispatch."""

import json
import os
import tempfile

import pytest

from src import server
from src.store import MemoryStore


@pytest.fixture(autouse=True)
def patch_store(monkeypatch, tmp_path):
    store = MemoryStore(db_path=str(tmp_path / "test.db"))
    monkeypatch.setattr(server, "store", store)
    return store


@pytest.mark.asyncio
async def test_brain_remember():
    result = await server.call_tool("brain_remember", {"category": "knowledge", "content": "test fact"})
    data = json.loads(result[0].text)
    assert data["status"] == "remembered"


@pytest.mark.asyncio
async def test_brain_recall(patch_store):
    patch_store.remember("knowledge", "Python is great")
    result = await server.call_tool("brain_recall", {"query": "Python"})
    data = json.loads(result[0].text)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_brain_forget(patch_store):
    mem = patch_store.remember("knowledge", "temp")
    result = await server.call_tool("brain_forget", {"id": mem["id"]})
    data = json.loads(result[0].text)
    assert data["status"] == "forgotten"


@pytest.mark.asyncio
async def test_brain_list(patch_store):
    patch_store.remember("people", "Alice", "team")
    result = await server.call_tool("brain_list", {"category": "people"})
    data = json.loads(result[0].text)
    assert len(data) == 1


@pytest.mark.asyncio
async def test_brain_profile_set_and_get():
    await server.call_tool("brain_profile", {"key": "name", "value": "Max"})
    result = await server.call_tool("brain_profile", {"key": "name"})
    data = json.loads(result[0].text)
    assert data["value"] == "Max"


@pytest.mark.asyncio
async def test_brain_context(patch_store):
    patch_store.remember("projects", "brAIn is an MCP server", "brain")
    result = await server.call_tool("brain_context", {"project": "brAIn"})
    data = json.loads(result[0].text)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_unknown_tool():
    result = await server.call_tool("brain_nonexistent", {})
    data = json.loads(result[0].text)
    assert "error" in data
