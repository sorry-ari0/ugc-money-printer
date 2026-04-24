import json
import os
import tempfile
import pytest
from ugc.analyzer.style_profiler import StyleProfiler


def test_analyze_hashtags():
    videos_meta = [
        {"hashtags": ["tech", "ai", "coding"], "duration": 30},
        {"hashtags": ["tech", "startup"], "duration": 15},
        {"hashtags": ["ai", "ml", "tech"], "duration": 45},
    ]
    result = StyleProfiler.analyze_hashtags(videos_meta)
    assert result["top_tags"][0] == "tech"
    assert result["avg_tags_per_post"] == 2.7  # (3+2+3)/3 = 2.67 rounded to 1dp


def test_analyze_pacing():
    videos_meta = [
        {"duration": 30},
        {"duration": 60},
        {"duration": 15},
    ]
    result = StyleProfiler.analyze_pacing(videos_meta)
    assert result["avg_duration"] == 35.0
    assert result["min_duration"] == 15
    assert result["max_duration"] == 60


def test_build_profile():
    videos_meta = [
        {"hashtags": ["tech"], "duration": 30, "views": 1000, "likes": 100},
        {"hashtags": ["ai"], "duration": 15, "views": 500, "likes": 50},
    ]
    profile = StyleProfiler.build_profile(videos_meta)
    assert "pacing" in profile
    assert "hashtags" in profile
    assert "engagement" in profile


def test_save_profile():
    with tempfile.TemporaryDirectory() as d:
        profile = {"pacing": {"avg_duration": 30}, "hashtags": {"top_tags": ["tech"]}}
        path = os.path.join(d, "style_profile.json")
        StyleProfiler.save_profile(profile, path)
        assert os.path.isfile(path)
        with open(path) as f:
            loaded = json.load(f)
        assert loaded["pacing"]["avg_duration"] == 30
