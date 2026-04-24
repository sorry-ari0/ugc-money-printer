import json
import os
from collections import Counter
from loguru import logger


class StyleProfiler:
    @staticmethod
    def analyze_hashtags(videos_meta: list) -> dict:
        all_tags = []
        tag_counts_per_post = []
        for v in videos_meta:
            tags = v.get("hashtags", [])
            all_tags.extend(tags)
            tag_counts_per_post.append(len(tags))

        counter = Counter(all_tags)
        top_tags = [tag for tag, _ in counter.most_common(20)]
        avg_count = (
            round(sum(tag_counts_per_post) / len(tag_counts_per_post), 1)
            if tag_counts_per_post else 0
        )
        return {
            "top_tags": top_tags,
            "tag_frequency": dict(counter.most_common(20)),
            "avg_tags_per_post": avg_count,
        }

    @staticmethod
    def analyze_pacing(videos_meta: list) -> dict:
        durations = [v.get("duration", 0) for v in videos_meta if v.get("duration")]
        if not durations:
            return {"avg_duration": 0, "min_duration": 0, "max_duration": 0}
        return {
            "avg_duration": round(sum(durations) / len(durations), 1),
            "min_duration": min(durations),
            "max_duration": max(durations),
        }

    @staticmethod
    def analyze_engagement(videos_meta: list) -> dict:
        views = [v.get("views", 0) for v in videos_meta]
        likes = [v.get("likes", 0) for v in videos_meta]
        if not views or sum(views) == 0:
            return {"avg_views": 0, "avg_likes": 0, "engagement_rate": 0}
        return {
            "avg_views": round(sum(views) / len(views), 1),
            "avg_likes": round(sum(likes) / len(likes), 1),
            "engagement_rate": round(sum(likes) / sum(views) * 100, 2),
        }

    @staticmethod
    def build_profile(videos_meta: list) -> dict:
        return {
            "pacing": StyleProfiler.analyze_pacing(videos_meta),
            "hashtags": StyleProfiler.analyze_hashtags(videos_meta),
            "engagement": StyleProfiler.analyze_engagement(videos_meta),
            "video_count": len(videos_meta),
        }

    @staticmethod
    def save_profile(profile: dict, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(profile, f, indent=2)
        logger.info(f"Style profile saved to {path}")

    @staticmethod
    def load_profile(path: str) -> dict:
        if not os.path.isfile(path):
            return {}
        with open(path, "r") as f:
            return json.load(f)
