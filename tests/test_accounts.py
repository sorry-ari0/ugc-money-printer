import json
import os
import tempfile
import pytest
from ugc.accounts import AccountManager


def _make_manager(tmp_dir: str) -> AccountManager:
    return AccountManager(accounts_dir=tmp_dir)


def test_add_account():
    with tempfile.TemporaryDirectory() as d:
        mgr = _make_manager(d)
        mgr.add("testuser")
        assert "testuser" in mgr.list_accounts()
        assert os.path.isdir(os.path.join(d, "testuser", "videos"))
        assert os.path.isfile(os.path.join(d, "testuser", "metadata.json"))


def test_add_strips_at_symbol():
    with tempfile.TemporaryDirectory() as d:
        mgr = _make_manager(d)
        mgr.add("@testuser")
        assert "testuser" in mgr.list_accounts()


def test_set_active():
    with tempfile.TemporaryDirectory() as d:
        mgr = _make_manager(d)
        mgr.add("user1")
        mgr.add("user2")
        mgr.set_active("user2")
        assert mgr.get_active() == "user2"


def test_set_active_unknown_raises():
    with tempfile.TemporaryDirectory() as d:
        mgr = _make_manager(d)
        with pytest.raises(ValueError):
            mgr.set_active("nonexistent")


def test_list_accounts():
    with tempfile.TemporaryDirectory() as d:
        mgr = _make_manager(d)
        mgr.add("a")
        mgr.add("b")
        assert set(mgr.list_accounts()) == {"a", "b"}


def test_first_added_becomes_active():
    with tempfile.TemporaryDirectory() as d:
        mgr = _make_manager(d)
        mgr.add("first")
        assert mgr.get_active() == "first"
