import os
import tempfile
import toml
import pytest
from ugc.config import UGCConfig
from ugc.accounts import AccountManager
from ugc.analyzer.style_profiler import StyleProfiler
from ugc.captioner.whisperx_captioner import WhisperXCaptioner, WordSegment
from ugc.enhancer.pipeline import EnhancePipeline, EnhanceOptions
from ugc.publisher.ayrshare import AyrsharePublisher
from ugc.scout.viral import ViralScout
from ugc.llm import LLMRouter


def test_full_config_to_accounts_flow():
    with tempfile.TemporaryDirectory() as d:
        cfg_path = os.path.join(d, "config.toml")
        with open(cfg_path, "w") as f:
            toml.dump({"ugc": {"active_account": "testacct", "output_dir": "out"}}, f)

        cfg = UGCConfig(cfg_path)
        assert cfg.active_account == "testacct"

        mgr = AccountManager(os.path.join(d, "accounts"))
        mgr.add("testacct")
        assert mgr.get_active() == "testacct"


def test_style_to_scout_flow():
    videos = [
        {"hashtags": ["ai", "tech"], "duration": 30, "views": 1000, "likes": 100,
         "caption": "Building AI tools #ai #tech"},
        {"hashtags": ["coding"], "duration": 45, "views": 500, "likes": 50,
         "caption": "Coding session #coding"},
    ]
    profile = StyleProfiler.build_profile(videos)
    assert profile["video_count"] == 2

    topics = ViralScout.extract_topics(videos)
    assert "ai" in topics


def test_caption_to_enhance_flow():
    segs = [
        WordSegment(word="Hello", start=0.0, end=0.5),
        WordSegment(word="world", start=0.6, end=1.0),
    ]
    srt = WhisperXCaptioner.format_srt(segs)
    ass = WhisperXCaptioner.format_ass(segs, style="word-pop")
    assert "Hello" in srt
    assert "Hello" in ass

    cmd = EnhancePipeline._build_caption_burn_cmd("/tmp/v.mp4", "/tmp/v.ass", "/tmp/out.mp4")
    assert len(cmd) > 5


def test_publisher_init():
    pub = AyrsharePublisher(api_key="test-key")
    assert pub.api_key == "test-key"
    mapped = pub._map_platforms(["tiktok", "invalid", "youtube"])
    assert "invalid" not in mapped
    assert "tiktok" in mapped


def test_llm_router_selection():
    router = LLMRouter("anthropic", "claude-sonnet-4-6", "ollama", "llama:latest", "sk-test")
    provider, model = router.select()
    assert provider == "anthropic"

    router2 = LLMRouter("anthropic", "claude-sonnet-4-6", "ollama", "llama:latest", "")
    provider2, model2 = router2.select()
    assert provider2 == "ollama"
