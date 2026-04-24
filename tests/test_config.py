import os
import tempfile
import toml
import pytest
from ugc.config import UGCConfig


def _write_config(tmp_dir: str, ugc_section: dict) -> str:
    cfg = {"ugc": ugc_section}
    path = os.path.join(tmp_dir, "config.toml")
    with open(path, "w") as f:
        toml.dump(cfg, f)
    return path


def test_loads_active_account():
    with tempfile.TemporaryDirectory() as d:
        path = _write_config(d, {"active_account": "testuser", "output_dir": "out"})
        cfg = UGCConfig(path)
        assert cfg.active_account == "testuser"


def test_defaults_when_missing():
    with tempfile.TemporaryDirectory() as d:
        path = _write_config(d, {})
        cfg = UGCConfig(path)
        assert cfg.active_account == "ari.from.jelly"
        assert cfg.output_dir == "storage/output"
        assert cfg.llm_primary == "anthropic"
        assert cfg.caption_style == "word-pop"
        assert cfg.platforms == ["tiktok", "instagram", "youtube", "twitter", "linkedin"]


def test_llm_section():
    with tempfile.TemporaryDirectory() as d:
        path = _write_config(d, {
            "llm": {"primary": "ollama", "primary_model": "qwen2.5:7b"}
        })
        cfg = UGCConfig(path)
        assert cfg.llm_primary == "ollama"
        assert cfg.llm_primary_model == "qwen2.5:7b"
