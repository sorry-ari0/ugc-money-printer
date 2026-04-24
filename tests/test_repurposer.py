import json
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from ugc.repurposer.linkedin import LinkedInRepurposer, LinkedInPost


def test_post_dataclass():
    post = LinkedInPost(
        title="How I built an AI app",
        body="Here's what I learned...",
        hashtags=["ai", "startup"],
        source_tiktok_id="123",
    )
    assert post.title == "How I built an AI app"
    assert len(post.hashtags) == 2


def test_format_post_with_hashtags():
    post = LinkedInPost(
        title="My Journey",
        body="Line 1\n\nLine 2",
        hashtags=["tech", "ai"],
        source_tiktok_id="456",
    )
    formatted = LinkedInRepurposer.format_post(post)
    assert "My Journey" in formatted
    assert "#tech" in formatted
    assert "#ai" in formatted
    assert len(formatted) <= 3000


def test_format_post_truncates():
    post = LinkedInPost(
        title="Title",
        body="x" * 5000,
        hashtags=[],
        source_tiktok_id="789",
    )
    formatted = LinkedInRepurposer.format_post(post)
    assert len(formatted) <= 3000


def test_extract_key_points():
    transcript = "So today I want to talk about how we built our app. First we chose the tech stack. Then we built the MVP. Finally we launched and got users."
    points = LinkedInRepurposer.extract_key_points(transcript)
    assert isinstance(points, list)
    assert len(points) >= 1


def test_build_prompt():
    prompt = LinkedInRepurposer.build_repurpose_prompt(
        transcript="I built an AI app and here's what happened",
        caption="Building in public #ai #startup",
        style_hints={"tone": "professional", "avg_post_length": 200},
    )
    assert "LinkedIn" in prompt
    assert "I built an AI app" in prompt
    assert "#ai" in prompt


def test_save_posts():
    with tempfile.TemporaryDirectory() as d:
        posts = [
            LinkedInPost(title="Post 1", body="Body 1", hashtags=["ai"], source_tiktok_id="1"),
            LinkedInPost(title="Post 2", body="Body 2", hashtags=["tech"], source_tiktok_id="2"),
        ]
        path = os.path.join(d, "linkedin_posts.json")
        LinkedInRepurposer.save_posts(posts, path)
        with open(path) as f:
            loaded = json.load(f)
        assert len(loaded) == 2
        assert loaded[0]["title"] == "Post 1"
