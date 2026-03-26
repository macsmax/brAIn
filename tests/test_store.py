"""Tests for MemoryStore."""

import pytest
from src.store import MemoryStore


@pytest.fixture
def store(tmp_path):
    return MemoryStore(db_path=str(tmp_path / "test.db"))


def test_remember_and_recall(store):
    result = store.remember("knowledge", "Python is a programming language", "python,lang")
    assert result["status"] == "remembered"
    assert "id" in result

    results = store.recall("Python programming")
    assert len(results) > 0
    assert "Python" in results[0]["content"]


def test_forget(store):
    mem = store.remember("knowledge", "temporary fact")
    result = store.forget(mem["id"])
    assert result["status"] == "forgotten"


def test_forget_nonexistent(store):
    result = store.forget("nonexistent")
    assert result["status"] == "not found"


def test_list_by_category(store):
    store.remember("people", "Alice is an engineer", "team")
    store.remember("projects", "brAIn is an MCP server")
    results = store.list_memories(category="people")
    assert len(results) == 1
    assert results[0]["category"] == "people"


def test_list_by_tag(store):
    store.remember("people", "Bob knows Rust", "rust,team")
    store.remember("people", "Carol knows Python", "python,team")
    results = store.list_memories(tag="rust")
    assert len(results) == 1


def test_list_all(store):
    store.remember("knowledge", "fact one")
    store.remember("knowledge", "fact two")
    results = store.list_memories()
    assert len(results) == 2


def test_profile_set_and_get(store):
    store.set_profile("name", "Max")
    result = store.get_profile("name")
    assert result["value"] == "Max"


def test_profile_get_missing(store):
    result = store.get_profile("nonexistent")
    assert result["value"] is None


def test_profile_get_all(store):
    store.set_profile("name", "Max")
    store.set_profile("team", "EC2")
    result = store.get_profile()
    assert result == {"name": "Max", "team": "EC2"}


def test_profile_upsert(store):
    store.set_profile("name", "Max")
    store.set_profile("name", "Maxwell")
    assert store.get_profile("name")["value"] == "Maxwell"


def test_context(store):
    store.remember("projects", "brAIn is a local MCP server", "brain")
    store.remember("knowledge", "brAIn uses SQLite", "brain")
    results = store.context("brAIn")
    assert len(results) > 0
