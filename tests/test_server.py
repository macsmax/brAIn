"""Tests for MCP server tool functions."""

import json
import pytest

from src import server
from src.store import MemoryStore


@pytest.fixture(autouse=True)
def patch_store(monkeypatch, tmp_path):
    store = MemoryStore(db_path=str(tmp_path / "test.db"))
    monkeypatch.setattr(server, "store", store)
    return store


def test_brain_remember():
    data = json.loads(server.brain_remember(category="knowledge", content="test fact"))
    assert data["status"] == "remembered"


def test_brain_recall(patch_store):
    patch_store.remember("knowledge", "Python is great")
    data = json.loads(server.brain_recall(query="Python"))
    assert len(data) > 0


def test_brain_forget(patch_store):
    mem = patch_store.remember("knowledge", "temp")
    data = json.loads(server.brain_forget(id=mem["id"]))
    assert data["status"] == "forgotten"


def test_brain_list(patch_store):
    patch_store.remember("people", "Alice", "team")
    data = json.loads(server.brain_list(category="people"))
    assert len(data) == 1


def test_brain_profile_set_and_get():
    server.brain_profile(key="name", value="Max")
    data = json.loads(server.brain_profile(key="name"))
    assert data["value"] == "Max"


def test_brain_context(patch_store):
    patch_store.remember("projects", "brAIn is an MCP server", "brain")
    data = json.loads(server.brain_context(project="brAIn"))
    assert len(data) > 0
