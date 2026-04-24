import json
import os
from dataclasses import dataclass, field
from typing import Optional
from loguru import logger

try:
    import requests
except ImportError:
    requests = None

CAPTION_LIMITS = {
    "tiktok": 2200,
    "instagram": 2200,
    "youtube": 5000,
    "twitter": 280,
    "linkedin": 3000,
}


@dataclass
class PostResult:
    platform: str
    success: bool
    post_id: str = ""
    url: str = ""
    error: str = ""


class AyrsharePublisher:
    API_URL = "https://app.ayrshare.com/api"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _map_platforms(self, platforms: list) -> list:
        valid = {"tiktok", "instagram", "youtube", "twitter", "linkedin",
                 "facebook", "pinterest", "threads", "reddit"}
        return [p for p in platforms if p in valid]

    def _fit_caption(self, caption: str, platform: str) -> str:
        limit = CAPTION_LIMITS.get(platform, 2200)
        if len(caption) <= limit:
            return caption
        return caption[: limit - 3] + "..."

    def publish(self, video_path: str, caption: str,
                platforms: list, hashtags: list = None,
                schedule: str = None) -> list:
        if not self.api_key:
            logger.error("Ayrshare API key not configured")
            return [PostResult(platform=p, success=False, error="No API key")
                    for p in platforms]

        mapped = self._map_platforms(platforms)
        if not mapped:
            return []

        payload = {
            "post": caption,
            "platforms": mapped,
            "mediaUrls": [video_path],
            "isVideo": True,
        }
        if hashtags:
            payload["hashTags"] = hashtags
        if schedule:
            payload["scheduleDate"] = schedule

        if requests is None:
            logger.error("requests package not installed. Install: pip install requests")
            return [PostResult(platform=p, success=False, error="requests not installed")
                    for p in mapped]

        try:
            resp = requests.post(
                f"{self.API_URL}/post",
                headers=self._headers(),
                json=payload,
                timeout=120,
            )
            data = resp.json()
        except Exception as e:
            logger.error(f"Ayrshare publish failed: {e}")
            return [PostResult(platform=p, success=False, error=str(e))
                    for p in mapped]

        results = []
        if "postIds" in data:
            for post in data.get("postIds", []):
                results.append(PostResult(
                    platform=post.get("platform", ""),
                    success=post.get("status", "") == "success",
                    post_id=post.get("id", ""),
                    url=post.get("postUrl", ""),
                ))
        else:
            for p in mapped:
                results.append(PostResult(
                    platform=p,
                    success=data.get("status") == "success",
                    post_id=data.get("id", ""),
                ))

        return results

    def save_post_results(self, results: list, output_path: str):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        data = [
            {"platform": r.platform, "success": r.success,
             "post_id": r.post_id, "url": r.url, "error": r.error}
            for r in results
        ]
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
