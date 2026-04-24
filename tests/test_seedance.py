import json
import os
from unittest.mock import MagicMock, patch, call
from ugc.avatar.seedance import SeedanceAvatar, SeedanceOptions, MODELS


def test_models_dict():
    assert "text-to-video" in MODELS
    assert "image-to-video" in MODELS
    assert "reference-to-video" in MODELS
    assert all(m.startswith("bytedance/seedance-2.0/") for m in MODELS.values())


def test_seedance_options_defaults():
    opts = SeedanceOptions()
    assert opts.resolution == "720p"
    assert opts.aspect_ratio == "9:16"
    assert opts.generate_audio is True
    assert opts.fast is False


def test_pick_model():
    with patch.dict(os.environ, {"FAL_KEY": "test"}):
        avatar = SeedanceAvatar(fal_key="test")
    assert avatar._pick_model("text-to-video") == "bytedance/seedance-2.0/text-to-video"
    assert avatar._pick_model("image-to-video", fast=True) == "bytedance/seedance-2.0/fast/image-to-video"


def test_pick_model_invalid():
    with patch.dict(os.environ, {"FAL_KEY": "test"}):
        avatar = SeedanceAvatar(fal_key="test")
    try:
        avatar._pick_model("nonexistent")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


@patch("ugc.avatar.seedance.fal_client")
def test_generate_clip_text_to_video(mock_fal):
    mock_fal.subscribe.return_value = {
        "video": {"url": "https://storage.example.com/clip.mp4", "content_type": "video/mp4", "file_size": 1234},
        "seed": 42,
    }
    avatar = SeedanceAvatar(fal_key="test")
    result = avatar.generate_clip("A person talking to camera")

    mock_fal.subscribe.assert_called_once()
    call_args = mock_fal.subscribe.call_args
    assert call_args[0][0] == "bytedance/seedance-2.0/text-to-video"
    assert result["video_url"] == "https://storage.example.com/clip.mp4"
    assert result["seed"] == 42


@patch("ugc.avatar.seedance.fal_client")
def test_generate_clip_image_to_video(mock_fal):
    mock_fal.subscribe.return_value = {
        "video": {"url": "https://example.com/out.mp4"},
        "seed": 7,
    }
    avatar = SeedanceAvatar(fal_key="test")
    result = avatar.generate_clip("Person speaking", image_url="https://example.com/face.jpg")

    call_args = mock_fal.subscribe.call_args
    assert call_args[0][0] == "bytedance/seedance-2.0/image-to-video"
    assert call_args[1]["arguments"]["image_url"] == "https://example.com/face.jpg"


@patch("ugc.avatar.seedance._requests")
def test_download_clip(mock_requests, tmp_path):
    mock_resp = MagicMock()
    mock_resp.iter_content.return_value = [b"fake video data"]
    mock_requests.get.return_value = mock_resp

    avatar = SeedanceAvatar(fal_key="test")
    out = avatar.download_clip("https://example.com/clip.mp4", str(tmp_path / "out.mp4"))

    assert os.path.isfile(out)
    with open(out, "rb") as f:
        assert f.read() == b"fake video data"


@patch("ugc.avatar.seedance.fal_client")
@patch("ugc.avatar.seedance._requests")
def test_generate_avatar_video(mock_requests, mock_fal, tmp_path):
    mock_fal.subscribe.return_value = {
        "video": {"url": "https://example.com/clip.mp4"},
        "seed": 1,
    }
    mock_resp = MagicMock()
    mock_resp.iter_content.return_value = [b"\x00" * 100]
    mock_requests.get.return_value = mock_resp

    script = {
        "hook": "Did you know?",
        "body": ["AI is everywhere."],
        "cta": "Follow for more.",
    }

    avatar = SeedanceAvatar(fal_key="test")

    with patch.object(avatar, "_concat_clips") as mock_concat:
        result = avatar.generate_avatar_video(
            script, "https://example.com/face.jpg", str(tmp_path), SeedanceOptions()
        )

    assert mock_fal.subscribe.call_count == 3  # hook + 1 body + cta
    assert result["sections"] == 3


def test_concat_clips(tmp_path):
    clips = []
    for i in range(3):
        p = str(tmp_path / f"clip_{i}.mp4")
        with open(p, "wb") as f:
            f.write(b"\x00" * 10)
        clips.append(p)

    out = str(tmp_path / "concat.mp4")

    with patch("ugc.avatar.seedance.subprocess.run") as mock_run:
        SeedanceAvatar._concat_clips(clips, out)
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "concat" in call_args
