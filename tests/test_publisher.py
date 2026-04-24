import pytest
from unittest.mock import patch, MagicMock
from ugc.publisher.ayrshare import AyrsharePublisher, PostResult


def test_platform_mapping():
    pub = AyrsharePublisher(api_key="test")
    mapped = pub._map_platforms(["tiktok", "instagram", "youtube", "twitter", "linkedin"])
    assert "tiktok" in mapped
    assert "instagram" in mapped
    assert "youtube" in mapped
    assert "twitter" in mapped
    assert "linkedin" in mapped


def test_caption_truncation():
    pub = AyrsharePublisher(api_key="test")
    long_caption = "x" * 5000
    result = pub._fit_caption(long_caption, "tiktok")
    assert len(result) <= 2200

    result_tw = pub._fit_caption(long_caption, "twitter")
    assert len(result_tw) <= 280


def test_post_result_dataclass():
    r = PostResult(platform="tiktok", success=True, post_id="123", url="https://example.com")
    assert r.platform == "tiktok"
    assert r.success is True
