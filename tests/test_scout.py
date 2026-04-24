import json
import os
import tempfile
import pytest
from ugc.scout.viral import ViralScout


def test_extract_topics_from_metadata():
    videos = [
        {"caption": "Building an AI app with Claude #ai #coding #startup", "hashtags": ["ai", "coding", "startup"]},
        {"caption": "How I built my SaaS #saas #indie #tech", "hashtags": ["saas", "indie", "tech"]},
        {"caption": "AI tools for developers #ai #devtools", "hashtags": ["ai", "devtools"]},
    ]
    topics = ViralScout.extract_topics(videos)
    assert "ai" in topics
    assert len(topics) <= 10


def test_rank_by_engagement():
    accounts = [
        {"handle": "a", "followers": 1000, "avg_views": 5000},
        {"handle": "b", "followers": 10000, "avg_views": 5000},
        {"handle": "c", "followers": 500, "avg_views": 3000},
    ]
    ranked = ViralScout.rank_by_virality(accounts)
    assert ranked[0]["handle"] == "c"  # 3000/500 = 6.0 highest ratio
    assert ranked[1]["handle"] == "a"  # 5000/1000 = 5.0


def test_build_trend_report():
    viral_posts = [
        {"hook_duration": 1.5, "has_music": True, "caption_style": "word-pop", "hashtags": ["ai"]},
        {"hook_duration": 2.0, "has_music": True, "caption_style": "word-pop", "hashtags": ["tech"]},
        {"hook_duration": 1.0, "has_music": False, "caption_style": "full-line", "hashtags": ["ai"]},
    ]
    report = ViralScout.build_trend_report(viral_posts)
    assert "avg_hook_duration" in report
    assert "music_usage_pct" in report
    assert report["music_usage_pct"] == pytest.approx(66.7, abs=0.1)


def test_save_trend_report():
    with tempfile.TemporaryDirectory() as d:
        report = {"avg_hook_duration": 1.5, "music_usage_pct": 66.7}
        path = os.path.join(d, "trend_report.json")
        ViralScout.save_report(report, path)
        with open(path) as f:
            loaded = json.load(f)
        assert loaded["avg_hook_duration"] == 1.5
