import os
from unittest.mock import patch, MagicMock
from ugc.avatar.sadtalker import SadTalkerGenerator


@patch("ugc.avatar.sadtalker.os.path.isfile", return_value=True)
def test_init(mock_isfile):
    gen = SadTalkerGenerator(
        sadtalker_dir="/fake/SadTalker",
        python_exe="/fake/python.exe",
    )
    assert gen.sadtalker_dir == "/fake/SadTalker"


def test_init_missing_python():
    try:
        SadTalkerGenerator(python_exe="/nonexistent/python.exe")
        assert False, "Should have raised"
    except FileNotFoundError:
        pass


@patch("ugc.avatar.sadtalker.os.path.isfile", return_value=True)
@patch("ugc.avatar.sadtalker.subprocess.run")
@patch("ugc.avatar.sadtalker.os.listdir", return_value=["output.mp4"])
@patch("ugc.avatar.sadtalker.os.path.getmtime", return_value=1000)
def test_generate_clip(mock_mtime, mock_listdir, mock_run, mock_isfile, tmp_path):
    mock_run.return_value = MagicMock(returncode=0)
    gen = SadTalkerGenerator(sadtalker_dir=str(tmp_path), python_exe="/fake/python.exe")
    result_dir = str(tmp_path / "results")
    os.makedirs(result_dir, exist_ok=True)

    clip = gen.generate_clip("face.png", "audio.wav", result_dir)
    assert clip.endswith("output.mp4")
    cmd = mock_run.call_args[0][0]
    assert "--cpu" in cmd
    assert "--still" in cmd


@patch("ugc.avatar.sadtalker.os.path.isfile", return_value=True)
@patch("ugc.avatar.sadtalker.subprocess.run")
def test_concat_clips(mock_run, mock_isfile, tmp_path):
    clips = []
    for i in range(3):
        p = str(tmp_path / f"clip_{i}.mp4")
        with open(p, "wb") as f:
            f.write(b"\x00" * 10)
        clips.append(p)

    out = str(tmp_path / "final.mp4")
    mock_run.return_value = MagicMock(returncode=0)
    SadTalkerGenerator._concat_clips(clips, out)
    mock_run.assert_called_once()
