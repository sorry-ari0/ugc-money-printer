Download TikTok videos for the active account (or specify with --account).

Usage: /download-tiktok [@handle]

Run the TikTok downloader:
1. Read config.toml for the active account (or use the provided handle)
2. Run `python -c "from ugc.downloader.tiktok import TikTokDownloader; from ugc.config import UGCConfig; cfg = UGCConfig(); dl = TikTokDownloader(cfg.videos_dir('$ARGUMENTS'), '$ARGUMENTS' or cfg.active_account); dl.download()"`
3. Report how many videos were downloaded
4. Suggest running /analyze-style next
