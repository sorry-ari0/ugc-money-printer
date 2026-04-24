import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from ugc.enhancer.pipeline import EnhancePipeline, EnhanceOptions


def test_enhance_options_defaults():
    opts = EnhanceOptions()
    assert opts.caption_style == "word-pop"
    assert opts.add_music is True
    assert opts.add_broll is True
    assert opts.formats == ["9:16"]
    assert opts.auto_publish is False


def test_enhance_options_custom():
    opts = EnhanceOptions(
        caption_style="full-line",
        add_music=False,
        formats=["9:16", "16:9"],
        platforms=["tiktok", "youtube"],
    )
    assert opts.caption_style == "full-line"
    assert opts.formats == ["9:16", "16:9"]


def test_build_ffmpeg_caption_cmd():
    cmd = EnhancePipeline._build_caption_burn_cmd(
        input_path="/tmp/video.mp4",
        ass_path="/tmp/video.ass",
        output_path="/tmp/output.mp4",
    )
    assert "ffmpeg" in cmd[0] or cmd[0] == "ffmpeg"
    assert "-i" in cmd
    assert "ass" in " ".join(cmd)


def test_build_resize_cmd_portrait():
    cmd = EnhancePipeline._build_resize_cmd(
        input_path="/tmp/video.mp4",
        output_path="/tmp/portrait.mp4",
        aspect="9:16",
    )
    assert "1080" in " ".join(cmd)
    assert "1920" in " ".join(cmd)


def test_build_resize_cmd_landscape():
    cmd = EnhancePipeline._build_resize_cmd(
        input_path="/tmp/video.mp4",
        output_path="/tmp/landscape.mp4",
        aspect="16:9",
    )
    assert "1920" in " ".join(cmd)
    assert "1080" in " ".join(cmd)


def test_build_resize_cmd_square():
    cmd = EnhancePipeline._build_resize_cmd(
        input_path="/tmp/video.mp4",
        output_path="/tmp/square.mp4",
        aspect="1:1",
    )
    assert "1080:1080" in " ".join(cmd) or ("1080" in " ".join(cmd))
