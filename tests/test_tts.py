import os
from unittest.mock import patch, MagicMock
from ugc.avatar.tts import EdgeTTSGenerator


def test_default_voice():
    tts = EdgeTTSGenerator()
    assert tts.voice == "en-US-GuyNeural"


def test_custom_voice():
    tts = EdgeTTSGenerator(voice="en-US-JennyNeural")
    assert tts.voice == "en-US-JennyNeural"


@patch("ugc.avatar.tts.subprocess.run")
def test_generate(mock_run, tmp_path):
    mock_run.return_value = MagicMock(returncode=0)
    tts = EdgeTTSGenerator()
    path = str(tmp_path / "test.mp3")
    result = tts.generate("Hello world", path)
    assert result == path
    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert "edge_tts" in cmd[2]
    assert "--voice" in cmd
    assert "en-US-GuyNeural" in cmd


@patch("ugc.avatar.tts.subprocess.run")
def test_generate_sections(mock_run, tmp_path):
    mock_run.return_value = MagicMock(returncode=0)
    tts = EdgeTTSGenerator()
    script = {
        "hook": "Did you know?",
        "body": ["Point one.", "Point two."],
        "cta": "Follow me!",
    }
    sections = tts.generate_sections(script, str(tmp_path))
    assert len(sections) == 4  # hook + 2 body + cta
    assert sections[0]["label"] == "hook"
    assert sections[1]["label"] == "body_1"
    assert sections[3]["label"] == "cta"
    assert mock_run.call_count == 4


@patch("ugc.avatar.tts.subprocess.run")
def test_generate_failure(mock_run, tmp_path):
    mock_run.return_value = MagicMock(returncode=1, stderr="TTS error")
    tts = EdgeTTSGenerator()
    try:
        tts.generate("test", str(tmp_path / "fail.mp3"))
        assert False, "Should have raised"
    except RuntimeError as e:
        assert "TTS error" in str(e)
