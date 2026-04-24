import pytest
from unittest.mock import patch, MagicMock
from ugc.cli import CLI


def test_cli_init():
    cli = CLI(config_path="nonexistent.toml")
    assert cli.config is not None


def test_cli_download(tmp_path):
    cli = CLI.__new__(CLI)
    cli.config = MagicMock()
    cli.config.active_account = "testuser"
    cli.config.videos_dir.return_value = str(tmp_path / "videos")
    cli.accounts = MagicMock()

    with patch("ugc.cli.TikTokDownloader") as mock_dl:
        mock_dl.return_value.download.return_value = [{"id": "1"}]
        result = cli.download_tiktok()
        assert len(result) == 1
        mock_dl.assert_called_once()


def test_cli_analyze(tmp_path):
    cli = CLI.__new__(CLI)
    cli.config = MagicMock()
    cli.config.account_dir.return_value = str(tmp_path)
    cli.llm = MagicMock()

    with patch("ugc.cli.TikTokDownloader") as mock_dl:
        mock_dl.return_value._collect_metadata.return_value = [
            {"hashtags": ["ai"], "duration": 30, "views": 100, "likes": 10}
        ]
        with patch("ugc.cli.StyleProfiler") as mock_sp:
            mock_sp.build_profile.return_value = {"pacing": {}}
            mock_sp.save_profile = MagicMock()
            result = cli.analyze_style()
            assert result is not None
