import json
import os
import tempfile
from unittest.mock import patch, MagicMock
import pytest
from ugc.downloader.tiktok import TikTokDownloader


def test_build_download_command():
    dl = TikTokDownloader(output_dir="/tmp/vids", handle="testuser")
    cmd = dl._build_command()
    assert "yt-dlp" in cmd[0]
    assert "https://www.tiktok.com/@testuser" in cmd
    assert any("/tmp/vids" in arg for arg in cmd)


def test_parse_metadata_from_info_json():
    info = {
        "id": "123",
        "title": "test video",
        "description": "test desc #hello #world",
        "view_count": 1000,
        "like_count": 50,
        "duration": 15,
        "upload_date": "20260401",
        "webpage_url": "https://tiktok.com/@user/video/123",
    }
    meta = TikTokDownloader._parse_video_metadata(info)
    assert meta["id"] == "123"
    assert meta["caption"] == "test desc #hello #world"
    assert meta["views"] == 1000
    assert meta["likes"] == 50
    assert meta["duration"] == 15
    assert meta["hashtags"] == ["hello", "world"]


def test_handle_strips_at():
    dl = TikTokDownloader(output_dir="/tmp", handle="@user")
    assert dl.handle == "user"
