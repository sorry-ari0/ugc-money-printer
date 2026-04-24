import json
import os
import re
from dataclasses import dataclass, field
from loguru import logger

LINKEDIN_CHAR_LIMIT = 3000


@dataclass
class LinkedInPost:
    title: str
    body: str
    hashtags: list = field(default_factory=list)
    source_tiktok_id: str = ""
    call_to_action: str = ""


class LinkedInRepurposer:
    @staticmethod
    def format_post(post: LinkedInPost) -> str:
        parts = []
        if post.title:
            parts.append(post.title)
            parts.append("")
        parts.append(post.body)
        if post.call_to_action:
            parts.append("")
            parts.append(post.call_to_action)
        if post.hashtags:
            parts.append("")
            parts.append(" ".join(f"#{tag}" for tag in post.hashtags))

        text = "\n".join(parts)
        if len(text) > LINKEDIN_CHAR_LIMIT:
            text = text[: LINKEDIN_CHAR_LIMIT - 3] + "..."
        return text

    @staticmethod
    def extract_key_points(transcript: str) -> list:
        sentences = re.split(r'[.!?]+', transcript)
        points = [s.strip() for s in sentences if len(s.strip()) > 20]
        return points[:5]

    @staticmethod
    def build_repurpose_prompt(transcript: str, caption: str = "",
                                style_hints: dict = None) -> str:
        hints = ""
        if style_hints:
            hints = f"\nStyle hints: {json.dumps(style_hints)}"

        return f"""Convert this TikTok video transcript into a professional LinkedIn post.

TikTok transcript:
{transcript}

TikTok caption: {caption}
{hints}

Requirements:
- Professional but authentic tone (not corporate-speak)
- Start with a hook line that stops the scroll
- Break into short paragraphs (2-3 sentences max each)
- Include a clear takeaway or lesson
- End with a question or call-to-action to drive engagement
- Add 3-5 relevant LinkedIn hashtags
- Keep under 2500 characters (LinkedIn sweet spot)
- Transform the casual TikTok style into LinkedIn-appropriate language
- Preserve the core message and insights

Return JSON:
{{"title": "hook line", "body": "full post text", "hashtags": ["tag1", "tag2"], "call_to_action": "closing question or CTA"}}"""

    def repurpose(self, transcript: str, caption: str, tiktok_id: str,
                  llm=None, style_hints: dict = None) -> LinkedInPost:
        prompt = self.build_repurpose_prompt(transcript, caption, style_hints)

        if llm:
            try:
                response = llm.chat(
                    prompt=prompt,
                    system="You are a LinkedIn content strategist who transforms short-form video content into engaging LinkedIn posts. Always return valid JSON.",
                )
                data = json.loads(response)
                return LinkedInPost(
                    title=data.get("title", ""),
                    body=data.get("body", ""),
                    hashtags=data.get("hashtags", []),
                    source_tiktok_id=tiktok_id,
                    call_to_action=data.get("call_to_action", ""),
                )
            except Exception as e:
                logger.warning(f"LLM repurpose failed: {e}")

        points = self.extract_key_points(transcript)
        body = "\n\n".join(points) if points else transcript[:500]
        hashtags = re.findall(r"#(\w+)", caption)
        return LinkedInPost(
            title=caption[:100] if caption else "Key Takeaways",
            body=body,
            hashtags=hashtags[:5],
            source_tiktok_id=tiktok_id,
        )

    def batch_repurpose(self, videos_meta: list, transcripts: dict,
                         llm=None, style_hints: dict = None) -> list:
        posts = []
        for video in videos_meta:
            vid_id = video.get("id", "")
            transcript = transcripts.get(vid_id, "")
            if not transcript:
                continue
            post = self.repurpose(
                transcript=transcript,
                caption=video.get("caption", ""),
                tiktok_id=vid_id,
                llm=llm,
                style_hints=style_hints,
            )
            posts.append(post)
        return posts

    @staticmethod
    def save_posts(posts: list, path: str):
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        data = [
            {
                "title": p.title,
                "body": p.body,
                "hashtags": p.hashtags,
                "source_tiktok_id": p.source_tiktok_id,
                "call_to_action": p.call_to_action,
                "formatted": LinkedInRepurposer.format_post(p),
            }
            for p in posts
        ]
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved {len(posts)} LinkedIn posts to {path}")
