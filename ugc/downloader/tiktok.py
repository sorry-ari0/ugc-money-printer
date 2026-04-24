import json
import os
import re
import subprocess
from glob import glob
from datetime import datetime, timezone
from loguru import logger


class TikTokDownloader:
    def __init__(self, output_dir: str, handle: str):
        self.handle = handle.lstrip("@")
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def _build_command(self) -> list:
        return [
            "yt-dlp",
            "--write-info-json",
            "--write-thumbnail",
            "--no-overwrites",
            "--restrict-filenames",
            "-o", os.path.join(self.output_dir, "%(id)s.%(ext)s"),
            f"https://www.tiktok.com/@{self.handle}",
        ]

    @staticmethod
    def _parse_video_metadata(info: dict) -> dict:
        desc = info.get("description") or info.get("title", "")
        hashtags = re.findall(r"#(\w+)", desc)
        return {
            "id": info.get("id", ""),
            "caption": desc,
            "hashtags": hashtags,
            "views": info.get("view_count", 0),
            "likes": info.get("like_count", 0),
            "duration": info.get("duration", 0),
            "upload_date": info.get("upload_date", ""),
            "url": info.get("webpage_url", ""),
        }

    def download(self) -> list:
        cmd = self._build_command()
        logger.info(f"Downloading TikToks for @{self.handle}")
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"yt-dlp failed: {e.stderr}")
            raise
        except FileNotFoundError:
            logger.error("yt-dlp not found. Install: pip install yt-dlp")
            raise

        return self._collect_metadata()

    def _collect_metadata(self) -> list:
        results = []
        for info_file in glob(os.path.join(self.output_dir, "*.info.json")):
            with open(info_file, "r", encoding="utf-8") as f:
                info = json.load(f)
            results.append(self._parse_video_metadata(info))
        return results

    def sync(self) -> list:
        """Incremental download — yt-dlp --no-overwrites skips existing files."""
        return self.download()
