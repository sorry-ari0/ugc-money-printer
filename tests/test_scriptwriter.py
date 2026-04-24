import json
import os
from unittest.mock import MagicMock, patch
from ugc.scriptwriter.writer import ScriptWriter

SAMPLE_SCRIPT = {
    "hook": "Did you know most people get this wrong?",
    "body": ["First, let me explain the basics.", "Here's the surprising truth.", "And this is how you fix it."],
    "cta": "Follow for more tips like this!",
    "suggested_broll": ["person thinking", "lightbulb moment", "typing on laptop"],
    "estimated_duration": 45,
    "hashtags": ["productivity", "lifehack", "learnontiktok"],
}

SAMPLE_JSON = json.dumps(SAMPLE_SCRIPT)


def test_write_script():
    llm = MagicMock()
    llm.chat.return_value = SAMPLE_JSON
    writer = ScriptWriter()
    result = writer.write_script("tips for productivity", {}, llm)
    assert result["hook"] == SAMPLE_SCRIPT["hook"]
    assert len(result["body"]) == 3
    assert result["cta"] == SAMPLE_SCRIPT["cta"]
    assert "suggested_broll" in result
    assert "hashtags" in result


def test_write_script_json_wrapped():
    llm = MagicMock()
    llm.chat.return_value = f"```json\n{SAMPLE_JSON}\n```"
    writer = ScriptWriter()
    result = writer.write_script("tips", {}, llm)
    assert result["hook"] == SAMPLE_SCRIPT["hook"]


def test_write_script_with_style_hints():
    llm = MagicMock()
    llm.chat.return_value = SAMPLE_JSON
    writer = ScriptWriter()
    hints = {
        "pacing": {"avg_duration": 32.5},
        "hashtags": {"top_tags": [("viral", 10), ("fyp", 8)]},
        "engagement": {"avg_views": 50000},
        "llm_themes": "productivity, self-improvement",
    }
    result = writer.write_script("tips", hints, llm)
    call_args = llm.chat.call_args
    assert "32" in call_args.kwargs.get("system", call_args[1].get("system", ""))


def test_format_teleprompter():
    text = ScriptWriter.format_teleprompter(SAMPLE_SCRIPT)
    assert "[HOOK]" in text
    assert "1." in text
    assert "2." in text
    assert "3." in text
    assert "[CTA]" in text


def test_save_script(tmp_path):
    path = os.path.join(str(tmp_path), "scripts", "test.json")
    ScriptWriter.save_script(SAMPLE_SCRIPT, path)
    with open(path) as f:
        loaded = json.load(f)
    assert loaded == SAMPLE_SCRIPT


def test_write_script_for_creator():
    llm = MagicMock()
    llm.chat.return_value = SAMPLE_JSON
    writer = ScriptWriter()
    with patch("ugc.scriptwriter.writer.StyleProfiler.load_profile", return_value={"pacing": {"avg_duration": 30}}):
        result = writer.write_script_for_creator("tips", "testuser", "/fake/accounts", llm)
    assert result["hook"] == SAMPLE_SCRIPT["hook"]
