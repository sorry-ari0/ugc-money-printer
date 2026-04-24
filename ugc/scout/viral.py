import json
import os
from collections import Counter
from loguru import logger


class ViralScout:
    @staticmethod
    def extract_topics(videos_meta: list, max_topics: int = 10) -> list:
        all_tags = []
        for v in videos_meta:
            all_tags.extend(v.get("hashtags", []))
        counter = Counter(all_tags)
        return [tag for tag, _ in counter.most_common(max_topics)]

    @staticmethod
    def rank_by_virality(accounts: list) -> list:
        for acct in accounts:
            followers = acct.get("followers", 1)
            if followers == 0:
                followers = 1
            acct["virality_ratio"] = acct.get("avg_views", 0) / followers
        return sorted(accounts, key=lambda x: x["virality_ratio"], reverse=True)

    @staticmethod
    def build_trend_report(viral_posts: list) -> dict:
        if not viral_posts:
            return {}

        hook_durations = [p.get("hook_duration", 0) for p in viral_posts]
        music_count = sum(1 for p in viral_posts if p.get("has_music"))
        caption_styles = Counter(p.get("caption_style", "unknown") for p in viral_posts)
        all_tags = []
        for p in viral_posts:
            all_tags.extend(p.get("hashtags", []))

        return {
            "avg_hook_duration": round(sum(hook_durations) / len(hook_durations), 1),
            "music_usage_pct": round(music_count / len(viral_posts) * 100, 1),
            "dominant_caption_style": caption_styles.most_common(1)[0][0],
            "trending_tags": [t for t, _ in Counter(all_tags).most_common(10)],
            "sample_size": len(viral_posts),
        }

    @staticmethod
    def save_report(report: dict, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(report, f, indent=2)
        logger.info(f"Trend report saved to {path}")

    @staticmethod
    def load_report(path: str) -> dict:
        if not os.path.isfile(path):
            return {}
        with open(path) as f:
            return json.load(f)

    def discover_accounts(self, topics: list, handle: str,
                          max_accounts: int = 20) -> list:
        """Search TikTok for accounts posting about these topics.
        Uses yt-dlp search to find videos, then extracts uploader info."""
        import subprocess
        discovered = []

        for topic in topics[:5]:
            try:
                result = subprocess.run(
                    ["yt-dlp", "--flat-playlist", "--dump-json",
                     f"ytsearch10:tiktok {topic}"],
                    capture_output=True, text=True, timeout=60
                )
                for line in result.stdout.strip().split("\n"):
                    if not line:
                        continue
                    try:
                        info = json.loads(line)
                        uploader = info.get("uploader", "")
                        if uploader and uploader != handle:
                            discovered.append({
                                "handle": uploader,
                                "followers": info.get("channel_follower_count", 0),
                                "avg_views": info.get("view_count", 0),
                                "topic": topic,
                            })
                    except json.JSONDecodeError:
                        continue
            except Exception as e:
                logger.warning(f"Scout search failed for topic '{topic}': {e}")

        seen = set()
        unique = []
        for acct in discovered:
            if acct["handle"] not in seen:
                seen.add(acct["handle"])
                unique.append(acct)
            if len(unique) >= max_accounts:
                break

        return self.rank_by_virality(unique)
