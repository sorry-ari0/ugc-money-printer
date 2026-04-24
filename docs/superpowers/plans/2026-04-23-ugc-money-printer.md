# UGC Money Printer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend a MoneyPrinterTurbo fork with a UGC layer: TikTok downloading, style analysis, footage-first enhancement, WhisperX captioning, multi-platform publishing, and viral scouting — all wired to Claude Code via MCP servers and slash commands.

**Architecture:** Six new modules under `ugc/` sit alongside the untouched MPT `app/` and `webui/`. They share MPT's FFmpeg/MoviePy rendering and config system. MCP configs in `.claude/settings.json` wire ffmpeg-mcp-lite, Pixa, and Ayrshare. Claude Code commands in `.claude/commands/` orchestrate both pipelines.

**Tech Stack:** Python 3.11, yt-dlp, WhisperX, MoviePy, FFmpeg, Anthropic SDK, Ollama, Ayrshare API, toml config

---

## File Structure

```
ugc/
├── __init__.py
├── config.py                 # UGC config loader (reads [ugc] from config.toml)
├── accounts.py               # Multi-account manager (accounts.json CRUD)
├── downloader/
│   ├── __init__.py
│   └── tiktok.py             # yt-dlp wrapper for TikTok profile downloads
├── captioner/
│   ├── __init__.py
│   └── whisperx_captioner.py # WhisperX transcription + ASS/SRT generation
├── analyzer/
│   ├── __init__.py
│   └── style_profiler.py     # FFmpeg scene detection + Claude analysis → style_profile.json
├── enhancer/
│   ├── __init__.py
│   └── pipeline.py           # Footage-first pipeline orchestrator
├── publisher/
│   ├── __init__.py
│   └── ayrshare.py           # Ayrshare API wrapper for multi-platform posting
├── scout/
│   ├── __init__.py
│   └── viral.py              # Viral account discovery + trend analysis
└── llm.py                    # LLM router (Claude primary, Ollama fallback)

tests/
├── __init__.py
├── test_config.py
├── test_accounts.py
├── test_downloader.py
├── test_captioner.py
├── test_analyzer.py
├── test_enhancer.py
├── test_publisher.py
├── test_scout.py
└── test_llm.py

.claude/
├── settings.json
└── commands/
    ├── download-tiktok.md
    ├── analyze-style.md
    ├── enhance.md
    ├── generate.md
    ├── publish.md
    ├── batch.md
    ├── account.md
    ├── scout.md
    ├── trends.md
    └── hooks.md

storage/
└── accounts/
    ├── accounts.json
    └── ari.from.jelly/
        ├── videos/
        ├── assets/
        ├── metadata.json
        ├── style_profile.json
        └── scouts/
            ├── discovered_accounts.json
            ├── trend_report.json
            ├── viral_posts/
            └── hooks_library/
```

---

### Task 1: Config & Dependencies

**Files:**
- Modify: `requirements.txt`
- Modify: `config.example.toml` (append `[ugc]` section)
- Create: `ugc/__init__.py`
- Create: `ugc/config.py`
- Create: `tests/__init__.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Add UGC dependencies to requirements.txt**

Append to the end of `requirements.txt`:

```
# UGC Pipeline
yt-dlp>=2024.12.0
whisperx>=3.1.0
anthropic>=0.40.0
ollama>=0.4.0
ayrshare>=2.0.0
```

- [ ] **Step 2: Add [ugc] section to config.example.toml**

Append to end of `config.example.toml`:

```toml

########## UGC Pipeline Settings ##########

[ugc]
active_account = "ari.from.jelly"
output_dir = "storage/output"

[ugc.llm]
primary = "anthropic"
primary_model = "claude-sonnet-4-6"
fallback = "ollama"
fallback_model = "llama-agent:latest"
anthropic_api_key = ""

[ugc.enhance]
default_caption_style = "word-pop"
default_music = true
silence_trim = true
auto_publish = false

[ugc.publish]
platforms = ["tiktok", "instagram", "youtube", "twitter", "linkedin"]
ayrshare_api_key = ""

[ugc.scout]
max_accounts = 20
refresh_interval_hours = 168
```

- [ ] **Step 3: Create ugc/__init__.py**

```python
```

(Empty file — package marker)

- [ ] **Step 4: Write failing test for config loader**

Create `tests/__init__.py` (empty) and `tests/test_config.py`:

```python
import os
import tempfile
import toml
import pytest
from ugc.config import UGCConfig


def _write_config(tmp_dir: str, ugc_section: dict) -> str:
    cfg = {"ugc": ugc_section}
    path = os.path.join(tmp_dir, "config.toml")
    with open(path, "w") as f:
        toml.dump(cfg, f)
    return path


def test_loads_active_account():
    with tempfile.TemporaryDirectory() as d:
        path = _write_config(d, {"active_account": "testuser", "output_dir": "out"})
        cfg = UGCConfig(path)
        assert cfg.active_account == "testuser"


def test_defaults_when_missing():
    with tempfile.TemporaryDirectory() as d:
        path = _write_config(d, {})
        cfg = UGCConfig(path)
        assert cfg.active_account == "ari.from.jelly"
        assert cfg.output_dir == "storage/output"
        assert cfg.llm_primary == "anthropic"
        assert cfg.caption_style == "word-pop"
        assert cfg.platforms == ["tiktok", "instagram", "youtube", "twitter", "linkedin"]


def test_llm_section():
    with tempfile.TemporaryDirectory() as d:
        path = _write_config(d, {
            "llm": {"primary": "ollama", "primary_model": "qwen2.5:7b"}
        })
        cfg = UGCConfig(path)
        assert cfg.llm_primary == "ollama"
        assert cfg.llm_primary_model == "qwen2.5:7b"
```

- [ ] **Step 5: Run test to verify it fails**

Run: `cd C:\Users\afoma\ugc-money-printer && python -m pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'ugc.config'`

- [ ] **Step 6: Implement ugc/config.py**

```python
import os
import toml


class UGCConfig:
    def __init__(self, config_path: str = ""):
        if not config_path:
            root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(root, "config.toml")

        raw = {}
        if os.path.isfile(config_path):
            raw = toml.load(config_path).get("ugc", {})

        self.active_account: str = raw.get("active_account", "ari.from.jelly")
        self.output_dir: str = raw.get("output_dir", "storage/output")

        llm = raw.get("llm", {})
        self.llm_primary: str = llm.get("primary", "anthropic")
        self.llm_primary_model: str = llm.get("primary_model", "claude-sonnet-4-6")
        self.llm_fallback: str = llm.get("fallback", "ollama")
        self.llm_fallback_model: str = llm.get("fallback_model", "llama-agent:latest")
        self.anthropic_api_key: str = llm.get("anthropic_api_key", "")

        enhance = raw.get("enhance", {})
        self.caption_style: str = enhance.get("default_caption_style", "word-pop")
        self.default_music: bool = enhance.get("default_music", True)
        self.silence_trim: bool = enhance.get("silence_trim", True)
        self.auto_publish: bool = enhance.get("auto_publish", False)

        publish = raw.get("publish", {})
        self.platforms: list = publish.get(
            "platforms", ["tiktok", "instagram", "youtube", "twitter", "linkedin"]
        )
        self.ayrshare_api_key: str = publish.get("ayrshare_api_key", "")

        scout = raw.get("scout", {})
        self.scout_max_accounts: int = scout.get("max_accounts", 20)
        self.scout_refresh_hours: int = scout.get("refresh_interval_hours", 168)

    @property
    def root_dir(self) -> str:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def account_dir(self, handle: str = "") -> str:
        h = handle or self.active_account
        return os.path.join(self.root_dir, "storage", "accounts", h)

    def videos_dir(self, handle: str = "") -> str:
        return os.path.join(self.account_dir(handle), "videos")

    def assets_dir(self, handle: str = "") -> str:
        return os.path.join(self.account_dir(handle), "assets")

    def scouts_dir(self, handle: str = "") -> str:
        return os.path.join(self.account_dir(handle), "scouts")
```

- [ ] **Step 7: Run test to verify it passes**

Run: `cd C:\Users\afoma\ugc-money-printer && python -m pytest tests/test_config.py -v`
Expected: 3 tests PASS

- [ ] **Step 8: Commit**

```bash
git add ugc/__init__.py ugc/config.py tests/__init__.py tests/test_config.py requirements.txt config.example.toml
git commit -m "feat: add UGC config loader and dependencies"
```

---

### Task 2: Multi-Account Manager

**Files:**
- Create: `ugc/accounts.py`
- Create: `tests/test_accounts.py`
- Create: `storage/accounts/accounts.json`
- Create: `storage/accounts/ari.from.jelly/metadata.json`

- [ ] **Step 1: Write failing test**

Create `tests/test_accounts.py`:

```python
import json
import os
import tempfile
import pytest
from ugc.accounts import AccountManager


def _make_manager(tmp_dir: str) -> AccountManager:
    return AccountManager(accounts_dir=tmp_dir)


def test_add_account():
    with tempfile.TemporaryDirectory() as d:
        mgr = _make_manager(d)
        mgr.add("testuser")
        assert "testuser" in mgr.list_accounts()
        assert os.path.isdir(os.path.join(d, "testuser", "videos"))
        assert os.path.isfile(os.path.join(d, "testuser", "metadata.json"))


def test_add_strips_at_symbol():
    with tempfile.TemporaryDirectory() as d:
        mgr = _make_manager(d)
        mgr.add("@testuser")
        assert "testuser" in mgr.list_accounts()


def test_set_active():
    with tempfile.TemporaryDirectory() as d:
        mgr = _make_manager(d)
        mgr.add("user1")
        mgr.add("user2")
        mgr.set_active("user2")
        assert mgr.get_active() == "user2"


def test_set_active_unknown_raises():
    with tempfile.TemporaryDirectory() as d:
        mgr = _make_manager(d)
        with pytest.raises(ValueError):
            mgr.set_active("nonexistent")


def test_list_accounts():
    with tempfile.TemporaryDirectory() as d:
        mgr = _make_manager(d)
        mgr.add("a")
        mgr.add("b")
        assert set(mgr.list_accounts()) == {"a", "b"}


def test_first_added_becomes_active():
    with tempfile.TemporaryDirectory() as d:
        mgr = _make_manager(d)
        mgr.add("first")
        assert mgr.get_active() == "first"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\afoma\ugc-money-printer && python -m pytest tests/test_accounts.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'ugc.accounts'`

- [ ] **Step 3: Implement ugc/accounts.py**

```python
import json
import os
from datetime import datetime, timezone


class AccountManager:
    def __init__(self, accounts_dir: str = ""):
        if not accounts_dir:
            root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            accounts_dir = os.path.join(root, "storage", "accounts")
        self._dir = accounts_dir
        self._index_path = os.path.join(self._dir, "accounts.json")
        self._data = self._load()

    def _load(self) -> dict:
        if os.path.isfile(self._index_path):
            with open(self._index_path, "r") as f:
                return json.load(f)
        return {"active": "", "accounts": []}

    def _save(self):
        os.makedirs(self._dir, exist_ok=True)
        with open(self._index_path, "w") as f:
            json.dump(self._data, f, indent=2)

    def add(self, handle: str):
        handle = handle.lstrip("@")
        if handle in self._data["accounts"]:
            return

        acct_dir = os.path.join(self._dir, handle)
        for sub in ["videos", "assets", "scouts/viral_posts", "scouts/hooks_library"]:
            os.makedirs(os.path.join(acct_dir, sub), exist_ok=True)

        metadata = {
            "handle": handle,
            "platform": "tiktok",
            "added_at": datetime.now(timezone.utc).isoformat(),
            "last_sync": None,
        }
        with open(os.path.join(acct_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)

        self._data["accounts"].append(handle)
        if not self._data["active"]:
            self._data["active"] = handle
        self._save()

    def set_active(self, handle: str):
        handle = handle.lstrip("@")
        if handle not in self._data["accounts"]:
            raise ValueError(f"Account '{handle}' not registered. Add it first.")
        self._data["active"] = handle
        self._save()

    def get_active(self) -> str:
        return self._data["active"]

    def list_accounts(self) -> list:
        return list(self._data["accounts"])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:\Users\afoma\ugc-money-printer && python -m pytest tests/test_accounts.py -v`
Expected: 6 tests PASS

- [ ] **Step 5: Seed ari.from.jelly account**

Create `storage/accounts/accounts.json`:

```json
{
  "active": "ari.from.jelly",
  "accounts": ["ari.from.jelly"]
}
```

Create `storage/accounts/ari.from.jelly/metadata.json`:

```json
{
  "handle": "ari.from.jelly",
  "platform": "tiktok",
  "added_at": "2026-04-23T00:00:00+00:00",
  "last_sync": null
}
```

- [ ] **Step 6: Commit**

```bash
git add ugc/accounts.py tests/test_accounts.py storage/accounts/accounts.json storage/accounts/ari.from.jelly/metadata.json
git commit -m "feat: add multi-account manager with ari.from.jelly"
```

---

### Task 3: TikTok Downloader

**Files:**
- Create: `ugc/downloader/__init__.py`
- Create: `ugc/downloader/tiktok.py`
- Create: `tests/test_downloader.py`

- [ ] **Step 1: Write failing test**

Create `ugc/downloader/__init__.py` (empty) and `tests/test_downloader.py`:

```python
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
import pytest
from ugc.downloader.tiktok import TikTokDownloader


def test_build_download_command():
    dl = TikTokDownloader(output_dir="/tmp/vids", handle="testuser")
    cmd = dl._build_command()
    assert "yt-dlp" in cmd[0]
    assert "https://www.tiktok.com/@testuser" in cmd
    assert any("/tmp/vids" in arg for arg in cmd)


def test_parse_metadata_from_info_json():
    info = {
        "id": "123",
        "title": "test video",
        "description": "test desc #hello #world",
        "view_count": 1000,
        "like_count": 50,
        "duration": 15,
        "upload_date": "20260401",
        "webpage_url": "https://tiktok.com/@user/video/123",
    }
    meta = TikTokDownloader._parse_video_metadata(info)
    assert meta["id"] == "123"
    assert meta["caption"] == "test desc #hello #world"
    assert meta["views"] == 1000
    assert meta["likes"] == 50
    assert meta["duration"] == 15
    assert meta["hashtags"] == ["hello", "world"]


def test_handle_strips_at():
    dl = TikTokDownloader(output_dir="/tmp", handle="@user")
    assert dl.handle == "user"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\afoma\ugc-money-printer && python -m pytest tests/test_downloader.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement ugc/downloader/tiktok.py**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:\Users\afoma\ugc-money-printer && python -m pytest tests/test_downloader.py -v`
Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add ugc/downloader/__init__.py ugc/downloader/tiktok.py tests/test_downloader.py
git commit -m "feat: add TikTok downloader with yt-dlp"
```

---

### Task 4: WhisperX Captioner

**Files:**
- Create: `ugc/captioner/__init__.py`
- Create: `ugc/captioner/whisperx_captioner.py`
- Create: `tests/test_captioner.py`

- [ ] **Step 1: Write failing test**

Create `ugc/captioner/__init__.py` (empty) and `tests/test_captioner.py`:

```python
import os
import tempfile
import pytest
from ugc.captioner.whisperx_captioner import WhisperXCaptioner, WordSegment


def test_format_srt_single_segment():
    segs = [WordSegment(word="Hello", start=0.0, end=0.5)]
    srt = WhisperXCaptioner.format_srt(segs)
    assert "1\n" in srt
    assert "00:00:00,000 --> 00:00:00,500" in srt
    assert "Hello" in srt


def test_format_srt_multiple_segments():
    segs = [
        WordSegment(word="Hello", start=0.0, end=0.5),
        WordSegment(word="world", start=0.6, end=1.0),
    ]
    srt = WhisperXCaptioner.format_srt(segs)
    assert "1\n" in srt
    assert "2\n" in srt


def test_format_ass_word_pop():
    segs = [
        WordSegment(word="Hello", start=0.0, end=0.5),
        WordSegment(word="world", start=0.6, end=1.0),
    ]
    ass = WhisperXCaptioner.format_ass(segs, style="word-pop")
    assert "[Script Info]" in ass
    assert "Hello" in ass
    assert "world" in ass


def test_format_ass_full_line():
    segs = [
        WordSegment(word="Hello", start=0.0, end=0.5),
        WordSegment(word="world", start=0.6, end=1.0),
    ]
    ass = WhisperXCaptioner.format_ass(segs, style="full-line")
    assert "Hello world" in ass


def test_group_words_into_lines():
    segs = [
        WordSegment(word="one", start=0.0, end=0.3),
        WordSegment(word="two", start=0.4, end=0.7),
        WordSegment(word="three", start=0.8, end=1.1),
        WordSegment(word="four", start=1.2, end=1.5),
        WordSegment(word="five", start=1.6, end=1.9),
    ]
    lines = WhisperXCaptioner.group_words(segs, max_words=3)
    assert len(lines) == 2
    assert len(lines[0]) == 3
    assert len(lines[1]) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\afoma\ugc-money-printer && python -m pytest tests/test_captioner.py -v`
Expected: FAIL

- [ ] **Step 3: Implement ugc/captioner/whisperx_captioner.py**

```python
import os
import subprocess
from dataclasses import dataclass
from typing import Optional
from loguru import logger


@dataclass
class WordSegment:
    word: str
    start: float
    end: float


class WhisperXCaptioner:
    def __init__(self, model_size: str = "large-v3", device: str = "cpu"):
        self.model_size = model_size
        self.device = device

    def transcribe(self, audio_path: str) -> list:
        try:
            import whisperx
        except ImportError:
            logger.error("whisperx not installed. Install: pip install whisperx")
            raise

        model = whisperx.load_model(self.model_size, self.device)
        audio = whisperx.load_audio(audio_path)
        result = model.transcribe(audio, batch_size=16)

        align_model, metadata = whisperx.load_align_model(
            language_code=result["language"], device=self.device
        )
        aligned = whisperx.align(
            result["segments"], align_model, metadata, audio, self.device
        )

        words = []
        for seg in aligned["word_segments"]:
            words.append(WordSegment(
                word=seg["word"],
                start=seg["start"],
                end=seg["end"],
            ))
        return words

    @staticmethod
    def group_words(segments: list, max_words: int = 4) -> list:
        lines = []
        current = []
        for seg in segments:
            current.append(seg)
            if len(current) >= max_words:
                lines.append(current)
                current = []
        if current:
            lines.append(current)
        return lines

    @staticmethod
    def _ts(seconds: float, fmt: str = "srt") -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        if fmt == "srt":
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
        cs = int((seconds % 1) * 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    @staticmethod
    def format_srt(segments: list) -> str:
        lines = []
        for i, seg in enumerate(segments, 1):
            start = WhisperXCaptioner._ts(seg.start, "srt")
            end = WhisperXCaptioner._ts(seg.end, "srt")
            lines.append(f"{i}\n{start} --> {end}\n{seg.word}\n")
        return "\n".join(lines)

    @staticmethod
    def format_ass(segments: list, style: str = "word-pop",
                   font: str = "Arial", font_size: int = 48,
                   primary_color: str = "&H00FFFFFF",
                   outline_color: str = "&H00000000") -> str:
        header = (
            "[Script Info]\n"
            "Title: UGC Captions\n"
            "ScriptType: v4.00+\n"
            "PlayResX: 1080\n"
            "PlayResY: 1920\n\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
            "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
            "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
            "Alignment, MarginL, MarginR, MarginV, Encoding\n"
            f"Style: Default,{font},{font_size},{primary_color},&H000000FF,"
            f"{outline_color},&H80000000,-1,0,0,0,100,100,0,0,1,3,0,2,40,40,200,1\n\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        )

        events = []
        ts = WhisperXCaptioner._ts

        if style == "word-pop":
            for seg in segments:
                start = ts(seg.start, "ass")
                end = ts(seg.end, "ass")
                text = r"{\fscx120\fscy120}" + seg.word
                events.append(
                    f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}"
                )
        elif style == "full-line":
            groups = WhisperXCaptioner.group_words(segments, max_words=6)
            for group in groups:
                start = ts(group[0].start, "ass")
                end = ts(group[-1].end, "ass")
                text = " ".join(s.word for s in group)
                events.append(
                    f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}"
                )
        elif style == "karaoke":
            groups = WhisperXCaptioner.group_words(segments, max_words=6)
            for group in groups:
                start = ts(group[0].start, "ass")
                end = ts(group[-1].end, "ass")
                parts = []
                for s in group:
                    dur_cs = int((s.end - s.start) * 100)
                    parts.append(r"{\kf" + str(dur_cs) + "}" + s.word)
                events.append(
                    f"Dialogue: 0,{start},{end},Default,,0,0,0,,{' '.join(parts)}"
                )
        else:
            for seg in segments:
                start = ts(seg.start, "ass")
                end = ts(seg.end, "ass")
                events.append(
                    f"Dialogue: 0,{start},{end},Default,,0,0,0,,{seg.word}"
                )

        return header + "\n".join(events) + "\n"

    def transcribe_and_save(self, audio_path: str, output_dir: str,
                            style: str = "word-pop") -> dict:
        segments = self.transcribe(audio_path)
        os.makedirs(output_dir, exist_ok=True)

        base = os.path.splitext(os.path.basename(audio_path))[0]
        srt_path = os.path.join(output_dir, f"{base}.srt")
        ass_path = os.path.join(output_dir, f"{base}.ass")

        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(self.format_srt(segments))
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(self.format_ass(segments, style=style))

        return {"srt": srt_path, "ass": ass_path, "segments": segments}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:\Users\afoma\ugc-money-printer && python -m pytest tests/test_captioner.py -v`
Expected: 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add ugc/captioner/__init__.py ugc/captioner/whisperx_captioner.py tests/test_captioner.py
git commit -m "feat: add WhisperX captioner with word-pop/full-line/karaoke styles"
```

---

### Task 5: LLM Router

**Files:**
- Create: `ugc/llm.py`
- Create: `tests/test_llm.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_llm.py`:

```python
from unittest.mock import patch, MagicMock
import pytest
from ugc.llm import LLMRouter


def test_route_to_primary():
    router = LLMRouter(
        primary="anthropic", primary_model="claude-sonnet-4-6",
        fallback="ollama", fallback_model="llama-agent:latest",
        anthropic_api_key="test-key"
    )
    assert router.primary == "anthropic"
    assert router.primary_model == "claude-sonnet-4-6"


def test_route_to_fallback_when_no_api_key():
    router = LLMRouter(
        primary="anthropic", primary_model="claude-sonnet-4-6",
        fallback="ollama", fallback_model="llama-agent:latest",
        anthropic_api_key=""
    )
    provider, model = router.select()
    assert provider == "ollama"
    assert model == "llama-agent:latest"


def test_route_to_primary_when_api_key_present():
    router = LLMRouter(
        primary="anthropic", primary_model="claude-sonnet-4-6",
        fallback="ollama", fallback_model="llama-agent:latest",
        anthropic_api_key="sk-test"
    )
    provider, model = router.select()
    assert provider == "anthropic"


@patch("ugc.llm.Anthropic")
def test_chat_anthropic(mock_cls):
    mock_client = MagicMock()
    mock_cls.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="response text")]
    )

    router = LLMRouter(
        primary="anthropic", primary_model="claude-sonnet-4-6",
        fallback="ollama", fallback_model="llama-agent:latest",
        anthropic_api_key="sk-test"
    )
    result = router.chat("Hello")
    assert result == "response text"
    mock_client.messages.create.assert_called_once()


@patch("ugc.llm.ollama_chat")
def test_chat_ollama(mock_chat):
    mock_chat.return_value = {"message": {"content": "ollama response"}}

    router = LLMRouter(
        primary="ollama", primary_model="llama-agent:latest",
        fallback="ollama", fallback_model="llama-agent:latest",
        anthropic_api_key=""
    )
    result = router.chat("Hello")
    assert result == "ollama response"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\afoma\ugc-money-printer && python -m pytest tests/test_llm.py -v`
Expected: FAIL

- [ ] **Step 3: Implement ugc/llm.py**

```python
from loguru import logger

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

try:
    from ollama import chat as ollama_chat
except ImportError:
    ollama_chat = None


class LLMRouter:
    def __init__(self, primary: str, primary_model: str,
                 fallback: str, fallback_model: str,
                 anthropic_api_key: str = ""):
        self.primary = primary
        self.primary_model = primary_model
        self.fallback = fallback
        self.fallback_model = fallback_model
        self.anthropic_api_key = anthropic_api_key

    def select(self) -> tuple:
        if self.primary == "anthropic" and self.anthropic_api_key:
            return self.primary, self.primary_model
        if self.primary == "ollama":
            return self.primary, self.primary_model
        return self.fallback, self.fallback_model

    def chat(self, prompt: str, system: str = "") -> str:
        provider, model = self.select()
        try:
            if provider == "anthropic":
                return self._chat_anthropic(prompt, system, model)
            else:
                return self._chat_ollama(prompt, system, model)
        except Exception as e:
            logger.warning(f"{provider} failed: {e}, trying fallback")
            if provider != self.fallback:
                return self._chat_ollama(prompt, system, self.fallback_model)
            raise

    def _chat_anthropic(self, prompt: str, system: str, model: str) -> str:
        if Anthropic is None:
            raise ImportError("anthropic package not installed")
        client = Anthropic(api_key=self.anthropic_api_key)
        kwargs = {
            "model": model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        resp = client.messages.create(**kwargs)
        return resp.content[0].text

    def _chat_ollama(self, prompt: str, system: str, model: str) -> str:
        if ollama_chat is None:
            raise ImportError("ollama package not installed")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = ollama_chat(model=model, messages=messages)
        return resp["message"]["content"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:\Users\afoma\ugc-money-printer && python -m pytest tests/test_llm.py -v`
Expected: 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add ugc/llm.py tests/test_llm.py
git commit -m "feat: add LLM router with Claude primary, Ollama fallback"
```

---

### Task 6: Style Analyzer

**Files:**
- Create: `ugc/analyzer/__init__.py`
- Create: `ugc/analyzer/style_profiler.py`
- Create: `tests/test_analyzer.py`

- [ ] **Step 1: Write failing test**

Create `ugc/analyzer/__init__.py` (empty) and `tests/test_analyzer.py`:

```python
import json
import os
import tempfile
import pytest
from ugc.analyzer.style_profiler import StyleProfiler


def test_analyze_hashtags():
    videos_meta = [
        {"hashtags": ["tech", "ai", "coding"], "duration": 30},
        {"hashtags": ["tech", "startup"], "duration": 15},
        {"hashtags": ["ai", "ml", "tech"], "duration": 45},
    ]
    result = StyleProfiler.analyze_hashtags(videos_meta)
    assert result["top_tags"][0] == "tech"
    assert result["avg_tags_per_post"] == 3.0  # (3+2+3)/3 = 2.67 rounded


def test_analyze_pacing():
    videos_meta = [
        {"duration": 30},
        {"duration": 60},
        {"duration": 15},
    ]
    result = StyleProfiler.analyze_pacing(videos_meta)
    assert result["avg_duration"] == 35.0
    assert result["min_duration"] == 15
    assert result["max_duration"] == 60


def test_build_profile():
    videos_meta = [
        {"hashtags": ["tech"], "duration": 30, "views": 1000, "likes": 100},
        {"hashtags": ["ai"], "duration": 15, "views": 500, "likes": 50},
    ]
    profile = StyleProfiler.build_profile(videos_meta)
    assert "pacing" in profile
    assert "hashtags" in profile
    assert "content" in profile


def test_save_profile():
    with tempfile.TemporaryDirectory() as d:
        profile = {"pacing": {"avg_duration": 30}, "hashtags": {"top_tags": ["tech"]}}
        path = os.path.join(d, "style_profile.json")
        StyleProfiler.save_profile(profile, path)
        assert os.path.isfile(path)
        with open(path) as f:
            loaded = json.load(f)
        assert loaded["pacing"]["avg_duration"] == 30
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\afoma\ugc-money-printer && python -m pytest tests/test_analyzer.py -v`
Expected: FAIL

- [ ] **Step 3: Implement ugc/analyzer/style_profiler.py**

```python
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
            "content": StyleProfiler.analyze_engagement(videos_meta),
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:\Users\afoma\ugc-money-printer && python -m pytest tests/test_analyzer.py -v`
Expected: 4 tests PASS (note: `test_analyze_hashtags` avg will be 2.7, fix expected to match)

Actually let's fix the test expectation: (3+2+3)/3 = 2.7, not 3.0.

Go back and fix `test_analyze_hashtags`:
```python
    assert result["avg_tags_per_post"] == 2.7
```

- [ ] **Step 5: Commit**

```bash
git add ugc/analyzer/__init__.py ugc/analyzer/style_profiler.py tests/test_analyzer.py
git commit -m "feat: add style profiler for pacing, hashtags, engagement analysis"
```

---

### Task 7: Publisher (Ayrshare)

**Files:**
- Create: `ugc/publisher/__init__.py`
- Create: `ugc/publisher/ayrshare.py`
- Create: `tests/test_publisher.py`

- [ ] **Step 1: Write failing test**

Create `ugc/publisher/__init__.py` (empty) and `tests/test_publisher.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from ugc.publisher.ayrshare import AyrsharePublisher, PostResult


def test_platform_mapping():
    pub = AyrsharePublisher(api_key="test")
    mapped = pub._map_platforms(["tiktok", "instagram", "youtube", "twitter", "linkedin"])
    assert "tiktok" in mapped
    assert "instagram" in mapped
    assert "youtube" in mapped
    assert "twitter" in mapped
    assert "linkedin" in mapped


def test_caption_truncation():
    pub = AyrsharePublisher(api_key="test")
    long_caption = "x" * 5000
    result = pub._fit_caption(long_caption, "tiktok")
    assert len(result) <= 2200

    result_tw = pub._fit_caption(long_caption, "twitter")
    assert len(result_tw) <= 280


def test_post_result_dataclass():
    r = PostResult(platform="tiktok", success=True, post_id="123", url="https://example.com")
    assert r.platform == "tiktok"
    assert r.success is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\afoma\ugc-money-printer && python -m pytest tests/test_publisher.py -v`
Expected: FAIL

- [ ] **Step 3: Implement ugc/publisher/ayrshare.py**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:\Users\afoma\ugc-money-printer && python -m pytest tests/test_publisher.py -v`
Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add ugc/publisher/__init__.py ugc/publisher/ayrshare.py tests/test_publisher.py
git commit -m "feat: add Ayrshare publisher for multi-platform posting"
```

---

### Task 8: Viral Scout

**Files:**
- Create: `ugc/scout/__init__.py`
- Create: `ugc/scout/viral.py`
- Create: `tests/test_scout.py`

- [ ] **Step 1: Write failing test**

Create `ugc/scout/__init__.py` (empty) and `tests/test_scout.py`:

```python
import json
import os
import tempfile
import pytest
from ugc.scout.viral import ViralScout


def test_extract_topics_from_metadata():
    videos = [
        {"caption": "Building an AI app with Claude #ai #coding #startup", "hashtags": ["ai", "coding", "startup"]},
        {"caption": "How I built my SaaS #saas #indie #tech", "hashtags": ["saas", "indie", "tech"]},
        {"caption": "AI tools for developers #ai #devtools", "hashtags": ["ai", "devtools"]},
    ]
    topics = ViralScout.extract_topics(videos)
    assert "ai" in topics
    assert len(topics) <= 10


def test_rank_by_engagement():
    accounts = [
        {"handle": "a", "followers": 1000, "avg_views": 5000},
        {"handle": "b", "followers": 10000, "avg_views": 5000},
        {"handle": "c", "followers": 500, "avg_views": 3000},
    ]
    ranked = ViralScout.rank_by_virality(accounts)
    assert ranked[0]["handle"] == "c"  # 3000/500 = 6.0 highest ratio
    assert ranked[1]["handle"] == "a"  # 5000/1000 = 5.0


def test_build_trend_report():
    viral_posts = [
        {"hook_duration": 1.5, "has_music": True, "caption_style": "word-pop", "hashtags": ["ai"]},
        {"hook_duration": 2.0, "has_music": True, "caption_style": "word-pop", "hashtags": ["tech"]},
        {"hook_duration": 1.0, "has_music": False, "caption_style": "full-line", "hashtags": ["ai"]},
    ]
    report = ViralScout.build_trend_report(viral_posts)
    assert "avg_hook_duration" in report
    assert "music_usage_pct" in report
    assert report["music_usage_pct"] == pytest.approx(66.7, abs=0.1)


def test_save_trend_report():
    with tempfile.TemporaryDirectory() as d:
        report = {"avg_hook_duration": 1.5, "music_usage_pct": 66.7}
        path = os.path.join(d, "trend_report.json")
        ViralScout.save_report(report, path)
        with open(path) as f:
            loaded = json.load(f)
        assert loaded["avg_hook_duration"] == 1.5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\afoma\ugc-money-printer && python -m pytest tests/test_scout.py -v`
Expected: FAIL

- [ ] **Step 3: Implement ugc/scout/viral.py**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:\Users\afoma\ugc-money-printer && python -m pytest tests/test_scout.py -v`
Expected: 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add ugc/scout/__init__.py ugc/scout/viral.py tests/test_scout.py
git commit -m "feat: add viral scout for trend discovery and account ranking"
```

---

### Task 9: Enhance Pipeline

**Files:**
- Create: `ugc/enhancer/__init__.py`
- Create: `ugc/enhancer/pipeline.py`
- Create: `tests/test_enhancer.py`

- [ ] **Step 1: Write failing test**

Create `ugc/enhancer/__init__.py` (empty) and `tests/test_enhancer.py`:

```python
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from ugc.enhancer.pipeline import EnhancePipeline, EnhanceOptions


def test_enhance_options_defaults():
    opts = EnhanceOptions()
    assert opts.caption_style == "word-pop"
    assert opts.add_music is True
    assert opts.add_broll is True
    assert opts.formats == ["9:16"]
    assert opts.auto_publish is False


def test_enhance_options_custom():
    opts = EnhanceOptions(
        caption_style="full-line",
        add_music=False,
        formats=["9:16", "16:9"],
        platforms=["tiktok", "youtube"],
    )
    assert opts.caption_style == "full-line"
    assert opts.formats == ["9:16", "16:9"]


def test_build_ffmpeg_caption_cmd():
    cmd = EnhancePipeline._build_caption_burn_cmd(
        input_path="/tmp/video.mp4",
        ass_path="/tmp/video.ass",
        output_path="/tmp/output.mp4",
    )
    assert "ffmpeg" in cmd[0] or cmd[0] == "ffmpeg"
    assert "-i" in cmd
    assert "ass" in " ".join(cmd)


def test_build_resize_cmd_portrait():
    cmd = EnhancePipeline._build_resize_cmd(
        input_path="/tmp/video.mp4",
        output_path="/tmp/portrait.mp4",
        aspect="9:16",
    )
    assert "1080" in " ".join(cmd)
    assert "1920" in " ".join(cmd)


def test_build_resize_cmd_landscape():
    cmd = EnhancePipeline._build_resize_cmd(
        input_path="/tmp/video.mp4",
        output_path="/tmp/landscape.mp4",
        aspect="16:9",
    )
    assert "1920" in " ".join(cmd)
    assert "1080" in " ".join(cmd)


def test_build_resize_cmd_square():
    cmd = EnhancePipeline._build_resize_cmd(
        input_path="/tmp/video.mp4",
        output_path="/tmp/square.mp4",
        aspect="1:1",
    )
    assert "1080:1080" in " ".join(cmd) or ("1080" in " ".join(cmd))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\afoma\ugc-money-printer && python -m pytest tests/test_enhancer.py -v`
Expected: FAIL

- [ ] **Step 3: Implement ugc/enhancer/pipeline.py**

```python
import os
import subprocess
from dataclasses import dataclass, field
from loguru import logger

ASPECT_RESOLUTIONS = {
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
    "1:1": (1080, 1080),
}


@dataclass
class EnhanceOptions:
    caption_style: str = "word-pop"
    add_music: bool = True
    add_broll: bool = True
    silence_trim: bool = True
    formats: list = field(default_factory=lambda: ["9:16"])
    platforms: list = field(default_factory=list)
    auto_publish: bool = False
    music_volume: float = 0.2
    music_path: str = ""


class EnhancePipeline:
    def __init__(self, config=None, llm=None, captioner=None, publisher=None):
        self.config = config
        self.llm = llm
        self.captioner = captioner
        self.publisher = publisher

    @staticmethod
    def _build_caption_burn_cmd(input_path: str, ass_path: str,
                                 output_path: str) -> list:
        ass_escaped = ass_path.replace("\\", "/").replace(":", "\\:")
        return [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", f"ass={ass_escaped}",
            "-c:v", "libx264", "-c:a", "aac",
            "-preset", "fast",
            output_path,
        ]

    @staticmethod
    def _build_resize_cmd(input_path: str, output_path: str,
                           aspect: str) -> list:
        w, h = ASPECT_RESOLUTIONS.get(aspect, (1080, 1920))
        return [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
                   f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black",
            "-c:v", "libx264", "-c:a", "aac",
            "-preset", "fast",
            output_path,
        ]

    @staticmethod
    def _build_music_mix_cmd(video_path: str, music_path: str,
                              output_path: str, volume: float = 0.2) -> list:
        return [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", music_path,
            "-filter_complex",
            f"[1:a]volume={volume}[bg];[0:a][bg]amix=inputs=2:duration=first[a]",
            "-map", "0:v", "-map", "[a]",
            "-c:v", "copy", "-c:a", "aac",
            output_path,
        ]

    def enhance(self, video_path: str, output_dir: str,
                options: EnhanceOptions = None) -> dict:
        if options is None:
            options = EnhanceOptions()

        os.makedirs(output_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(video_path))[0]
        results = {"source": video_path, "outputs": [], "captions": None}

        current = video_path

        if self.captioner:
            logger.info("Transcribing with WhisperX...")
            cap_result = self.captioner.transcribe_and_save(
                current, output_dir, style=options.caption_style
            )
            results["captions"] = cap_result

            captioned_path = os.path.join(output_dir, f"{base}_captioned.mp4")
            cmd = self._build_caption_burn_cmd(current, cap_result["ass"], captioned_path)
            subprocess.run(cmd, check=True, capture_output=True)
            current = captioned_path

        if options.add_music and options.music_path:
            logger.info("Mixing background music...")
            music_path = os.path.join(output_dir, f"{base}_music.mp4")
            cmd = self._build_music_mix_cmd(current, options.music_path,
                                             music_path, options.music_volume)
            subprocess.run(cmd, check=True, capture_output=True)
            current = music_path

        for aspect in options.formats:
            logger.info(f"Rendering {aspect} format...")
            suffix = aspect.replace(":", "x")
            out_path = os.path.join(output_dir, f"{base}_{suffix}.mp4")
            cmd = self._build_resize_cmd(current, out_path, aspect)
            subprocess.run(cmd, check=True, capture_output=True)
            results["outputs"].append({"aspect": aspect, "path": out_path})

        if options.auto_publish and self.publisher and options.platforms:
            logger.info("Publishing to platforms...")
            primary_output = results["outputs"][0]["path"]
            post_results = self.publisher.publish(
                primary_output, "", options.platforms
            )
            results["publish"] = post_results

        return results
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:\Users\afoma\ugc-money-printer && python -m pytest tests/test_enhancer.py -v`
Expected: 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add ugc/enhancer/__init__.py ugc/enhancer/pipeline.py tests/test_enhancer.py
git commit -m "feat: add enhance pipeline with caption burn, resize, music mix"
```

---

### Task 10: Claude Code Commands & MCP Config

**Files:**
- Create: `.claude/settings.json`
- Create: `.claude/commands/download-tiktok.md`
- Create: `.claude/commands/analyze-style.md`
- Create: `.claude/commands/enhance.md`
- Create: `.claude/commands/generate.md`
- Create: `.claude/commands/publish.md`
- Create: `.claude/commands/batch.md`
- Create: `.claude/commands/account.md`
- Create: `.claude/commands/scout.md`
- Create: `.claude/commands/trends.md`
- Create: `.claude/commands/hooks.md`

- [ ] **Step 1: Create .claude/settings.json**

```json
{
  "mcpServers": {
    "ffmpeg-mcp-lite": {
      "command": "python",
      "args": ["-m", "ffmpeg_mcp_lite"],
      "env": {}
    },
    "pixa": {
      "command": "npx",
      "args": ["-y", "pixa-mcp"],
      "env": {
        "PIXA_API_KEY": ""
      }
    },
    "ayrshare": {
      "command": "npx",
      "args": ["-y", "ayrshare-mcp"],
      "env": {
        "AYRSHARE_API_KEY": ""
      }
    }
  }
}
```

- [ ] **Step 2: Create slash commands**

`.claude/commands/download-tiktok.md`:
```markdown
Download TikTok videos for the active account (or specify with --account).

Usage: /download-tiktok [@handle]

Run the TikTok downloader:
1. Read config.toml for the active account (or use the provided handle)
2. Run `python -c "from ugc.downloader.tiktok import TikTokDownloader; from ugc.config import UGCConfig; cfg = UGCConfig(); dl = TikTokDownloader(cfg.videos_dir('$ARGUMENTS'), '$ARGUMENTS' or cfg.active_account); dl.download()"`
3. Report how many videos were downloaded
4. Suggest running /analyze-style next
```

`.claude/commands/analyze-style.md`:
```markdown
Build or refresh the style profile for the active account.

Usage: /analyze-style [@handle]

1. Read the account's downloaded video metadata from storage/accounts/{handle}/videos/
2. Collect all .info.json files and parse them
3. Run StyleProfiler.build_profile() on the metadata
4. Use Claude to analyze content themes and patterns from the captions
5. Save to storage/accounts/{handle}/style_profile.json
6. Display a summary of the style profile
```

`.claude/commands/enhance.md`:
```markdown
Enhance a raw video with captions, b-roll, music, and publish.

Usage: /enhance <video_path> [--no-broll] [--no-music] [--platforms tiktok,youtube] [--style word-pop|full-line|karaoke] [--dry-run]

Steps:
1. Load the active account's style_profile.json for defaults
2. Transcribe with WhisperX (word-level timestamps)
3. Analyze content with Claude (identify hook, key points, CTA)
4. Optionally inject b-roll from Pexels or the account's video library
5. Burn captions (default: word-pop style from profile)
6. Mix background music (from resource/songs/)
7. Render all formats: 9:16 (primary), 16:9, 1:1
8. If not --dry-run, publish via Ayrshare to selected platforms
9. Save results to storage/output/
```

`.claude/commands/generate.md`:
```markdown
Generate a video from a topic using MoneyPrinterTurbo's pipeline.

Usage: /generate <topic> [--trending] [--account handle]

Steps:
1. If --trending, load the active account's trend report and apply trending formats
2. Load the active account's style_profile.json for caption/pacing defaults
3. Use the MPT API to generate the video (call the FastAPI endpoint or invoke directly)
4. Apply the account's caption style
5. Output to storage/output/
```

`.claude/commands/publish.md`:
```markdown
Publish a rendered video to social platforms.

Usage: /publish <video_path> [--platforms tiktok,instagram,youtube,twitter,linkedin] [--caption "text"] [--schedule "2026-04-24T10:00:00Z"]

Steps:
1. Read config.toml for Ayrshare API key and default platforms
2. If no caption provided, generate one with Claude based on the video
3. Publish via AyrsharePublisher
4. Save post results to storage/output/posts/
```

`.claude/commands/batch.md`:
```markdown
Process a folder of raw clips through the enhance pipeline.

Usage: /batch <folder_path> [--style word-pop] [--platforms tiktok,youtube]

Steps:
1. Find all .mp4/.mov files in the folder
2. Run /enhance on each one sequentially
3. Report results summary at the end
```

`.claude/commands/account.md`:
```markdown
Manage TikTok accounts.

Usage:
  /account add @handle    — Register a new account
  /account use @handle    — Switch active account
  /account list           — Show all accounts and active one

Steps:
1. Parse the subcommand (add/use/list)
2. Use AccountManager from ugc.accounts
3. For 'add': create account directory structure, start initial download
4. For 'use': switch active account in accounts.json
5. For 'list': display all accounts with active indicator
```

`.claude/commands/scout.md`:
```markdown
Discover viral accounts in your niche.

Usage: /scout [--topics "ai, coding"] [--max 20]

Steps:
1. Load the active account's video metadata
2. Extract topics from hashtags (or use provided topics)
3. Search TikTok for accounts posting similar content
4. Rank by virality ratio (views/followers)
5. Download top posts from discovered accounts
6. Save to storage/accounts/{handle}/scouts/
7. Display top 10 discovered accounts
```

`.claude/commands/trends.md`:
```markdown
Show the latest trend report for the active account.

Usage: /trends

Steps:
1. Load storage/accounts/{handle}/scouts/trend_report.json
2. Display: avg hook duration, music usage %, dominant caption style, trending tags
3. If no report exists, suggest running /scout first
```

`.claude/commands/hooks.md`:
```markdown
Browse extracted hook clips from viral posts.

Usage: /hooks [--topic "ai"]

Steps:
1. List files in storage/accounts/{handle}/scouts/hooks_library/
2. Display metadata for each hook (source account, duration, topic)
3. If --topic, filter to matching hooks
```

- [ ] **Step 3: Commit**

```bash
git add .claude/settings.json .claude/commands/
git commit -m "feat: add Claude Code commands and MCP server config"
```

---

### Task 11: Wire Everything Together — CLI Entry Point

**Files:**
- Create: `ugc/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_cli.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\afoma\ugc-money-printer && python -m pytest tests/test_cli.py -v`
Expected: FAIL

- [ ] **Step 3: Implement ugc/cli.py**

```python
import os
from loguru import logger
from ugc.config import UGCConfig
from ugc.accounts import AccountManager
from ugc.downloader.tiktok import TikTokDownloader
from ugc.captioner.whisperx_captioner import WhisperXCaptioner
from ugc.analyzer.style_profiler import StyleProfiler
from ugc.enhancer.pipeline import EnhancePipeline, EnhanceOptions
from ugc.publisher.ayrshare import AyrsharePublisher
from ugc.scout.viral import ViralScout
from ugc.llm import LLMRouter


class CLI:
    def __init__(self, config_path: str = ""):
        self.config = UGCConfig(config_path)
        accts_dir = os.path.join(self.config.root_dir, "storage", "accounts")
        self.accounts = AccountManager(accts_dir)
        self.llm = LLMRouter(
            primary=self.config.llm_primary,
            primary_model=self.config.llm_primary_model,
            fallback=self.config.llm_fallback,
            fallback_model=self.config.llm_fallback_model,
            anthropic_api_key=self.config.anthropic_api_key,
        )
        self.captioner = WhisperXCaptioner()
        self.publisher = AyrsharePublisher(self.config.ayrshare_api_key)
        self.scout = ViralScout()

    def download_tiktok(self, handle: str = "") -> list:
        handle = handle or self.config.active_account
        dl = TikTokDownloader(
            output_dir=self.config.videos_dir(handle),
            handle=handle,
        )
        results = dl.download()
        logger.success(f"Downloaded {len(results)} videos for @{handle}")
        return results

    def analyze_style(self, handle: str = "") -> dict:
        handle = handle or self.config.active_account
        dl = TikTokDownloader(
            output_dir=self.config.videos_dir(handle),
            handle=handle,
        )
        videos_meta = dl._collect_metadata()
        if not videos_meta:
            logger.warning(f"No videos found for @{handle}. Run download first.")
            return {}

        profile = StyleProfiler.build_profile(videos_meta)

        try:
            captions = "\n".join(v.get("caption", "") for v in videos_meta[:20])
            analysis = self.llm.chat(
                prompt=f"Analyze these TikTok captions and identify the top 5 content themes/niches:\n\n{captions}",
                system="You are a social media analyst. Return a JSON list of themes.",
            )
            profile["llm_themes"] = analysis
        except Exception as e:
            logger.warning(f"LLM analysis skipped: {e}")

        profile_path = os.path.join(self.config.account_dir(handle), "style_profile.json")
        StyleProfiler.save_profile(profile, profile_path)
        return profile

    def enhance(self, video_path: str, options: EnhanceOptions = None) -> dict:
        if options is None:
            options = EnhanceOptions(
                caption_style=self.config.caption_style,
                add_music=self.config.default_music,
                auto_publish=self.config.auto_publish,
                platforms=self.config.platforms,
            )
        output_dir = os.path.join(self.config.output_dir, "enhanced")
        pipeline = EnhancePipeline(
            config=self.config,
            llm=self.llm,
            captioner=self.captioner,
            publisher=self.publisher,
        )
        return pipeline.enhance(video_path, output_dir, options)

    def publish(self, video_path: str, caption: str = "",
                platforms: list = None, schedule: str = None) -> list:
        platforms = platforms or self.config.platforms
        if not caption:
            try:
                caption = self.llm.chat(
                    prompt="Write a short, engaging social media caption for a video post. Keep it under 200 characters.",
                    system="You are a social media copywriter.",
                )
            except Exception:
                caption = ""
        return self.publisher.publish(video_path, caption, platforms, schedule=schedule)

    def scout_viral(self, topics: list = None, handle: str = "") -> dict:
        handle = handle or self.config.active_account
        if not topics:
            dl = TikTokDownloader(
                output_dir=self.config.videos_dir(handle), handle=handle
            )
            meta = dl._collect_metadata()
            topics = ViralScout.extract_topics(meta)

        accounts = self.scout.discover_accounts(
            topics, handle, self.config.scout_max_accounts
        )

        report_dir = self.config.scouts_dir(handle)
        ViralScout.save_report(
            {"discovered_accounts": accounts, "topics": topics},
            os.path.join(report_dir, "discovered_accounts.json"),
        )

        return {"accounts": accounts, "topics": topics}

    def get_trends(self, handle: str = "") -> dict:
        handle = handle or self.config.active_account
        path = os.path.join(self.config.scouts_dir(handle), "trend_report.json")
        return ViralScout.load_report(path)

    def switch_account(self, handle: str):
        self.accounts.set_active(handle)
        self.config.active_account = handle
        logger.info(f"Switched to @{handle}")

    def add_account(self, handle: str):
        self.accounts.add(handle)
        logger.info(f"Added @{handle}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:\Users\afoma\ugc-money-printer && python -m pytest tests/test_cli.py -v`
Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add ugc/cli.py tests/test_cli.py
git commit -m "feat: add CLI entry point wiring all UGC modules together"
```

---

### Task 12: Update config.toml & Final Integration Test

**Files:**
- Modify: `config.example.toml` (already done in Task 1, verify)
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration test**

Create `tests/test_integration.py`:

```python
import os
import tempfile
import toml
import pytest
from ugc.config import UGCConfig
from ugc.accounts import AccountManager
from ugc.analyzer.style_profiler import StyleProfiler
from ugc.captioner.whisperx_captioner import WhisperXCaptioner, WordSegment
from ugc.enhancer.pipeline import EnhancePipeline, EnhanceOptions
from ugc.publisher.ayrshare import AyrsharePublisher
from ugc.scout.viral import ViralScout
from ugc.llm import LLMRouter


def test_full_config_to_accounts_flow():
    with tempfile.TemporaryDirectory() as d:
        cfg_path = os.path.join(d, "config.toml")
        with open(cfg_path, "w") as f:
            toml.dump({"ugc": {"active_account": "testacct", "output_dir": "out"}}, f)

        cfg = UGCConfig(cfg_path)
        assert cfg.active_account == "testacct"

        mgr = AccountManager(os.path.join(d, "accounts"))
        mgr.add("testacct")
        assert mgr.get_active() == "testacct"


def test_style_to_scout_flow():
    videos = [
        {"hashtags": ["ai", "tech"], "duration": 30, "views": 1000, "likes": 100,
         "caption": "Building AI tools #ai #tech"},
        {"hashtags": ["coding"], "duration": 45, "views": 500, "likes": 50,
         "caption": "Coding session #coding"},
    ]
    profile = StyleProfiler.build_profile(videos)
    assert profile["video_count"] == 2

    topics = ViralScout.extract_topics(videos)
    assert "ai" in topics


def test_caption_to_enhance_flow():
    segs = [
        WordSegment(word="Hello", start=0.0, end=0.5),
        WordSegment(word="world", start=0.6, end=1.0),
    ]
    srt = WhisperXCaptioner.format_srt(segs)
    ass = WhisperXCaptioner.format_ass(segs, style="word-pop")
    assert "Hello" in srt
    assert "Hello" in ass

    cmd = EnhancePipeline._build_caption_burn_cmd("/tmp/v.mp4", "/tmp/v.ass", "/tmp/out.mp4")
    assert len(cmd) > 5


def test_publisher_init():
    pub = AyrsharePublisher(api_key="test-key")
    assert pub.api_key == "test-key"
    mapped = pub._map_platforms(["tiktok", "invalid", "youtube"])
    assert "invalid" not in mapped
    assert "tiktok" in mapped


def test_llm_router_selection():
    router = LLMRouter("anthropic", "claude-sonnet-4-6", "ollama", "llama:latest", "sk-test")
    provider, model = router.select()
    assert provider == "anthropic"

    router2 = LLMRouter("anthropic", "claude-sonnet-4-6", "ollama", "llama:latest", "")
    provider2, model2 = router2.select()
    assert provider2 == "ollama"
```

- [ ] **Step 2: Run integration test**

Run: `cd C:\Users\afoma\ugc-money-printer && python -m pytest tests/test_integration.py -v`
Expected: 5 tests PASS

- [ ] **Step 3: Run all tests**

Run: `cd C:\Users\afoma\ugc-money-printer && python -m pytest tests/ -v`
Expected: All tests PASS (approximately 31 tests)

- [ ] **Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "feat: add integration tests for full UGC pipeline"
```

---

### Task 13: Add .gitignore entries and CLAUDE.md

**Files:**
- Modify: `.gitignore`
- Create: `CLAUDE.md`

- [ ] **Step 1: Add storage to .gitignore**

Append to `.gitignore`:

```
# UGC storage (downloaded videos, generated content)
storage/accounts/*/videos/
storage/accounts/*/assets/
storage/accounts/*/scouts/viral_posts/
storage/accounts/*/scouts/hooks_library/
storage/output/

# Keep structure files
!storage/accounts/accounts.json
!storage/accounts/*/metadata.json
```

- [ ] **Step 2: Create CLAUDE.md**

```markdown
# UGC Money Printer

Fork of MoneyPrinterTurbo extended with a UGC creation pipeline.

## Quick Start

1. `pip install -r requirements.txt`
2. Copy `config.example.toml` to `config.toml` and fill in API keys
3. Use Claude Code commands: `/download-tiktok`, `/enhance`, `/generate`, `/scout`

## Architecture

- `app/` — Original MPT (do not modify)
- `ugc/` — UGC layer (downloader, analyzer, enhancer, captioner, publisher, scout)
- `.claude/commands/` — Claude Code slash commands
- `storage/accounts/` — Per-account data (videos, style profiles, scout data)

## Key Commands

- `/download-tiktok` — Sync TikTok videos for active account
- `/analyze-style` — Build style profile from downloaded videos
- `/enhance video.mp4` — Full pipeline: captions → b-roll → music → publish
- `/generate "topic"` — Generate video from scratch using MPT pipeline
- `/scout` — Discover viral accounts in your niche
- `/account add/use/list` — Manage TikTok accounts

## Config

All UGC settings are in `config.toml` under `[ugc]`. API keys:
- `[ugc.llm]` — Anthropic API key
- `[ugc.publish]` — Ayrshare API key

## Tests

```bash
python -m pytest tests/ -v
```
```

- [ ] **Step 3: Commit**

```bash
git add .gitignore CLAUDE.md
git commit -m "docs: add CLAUDE.md and .gitignore for UGC storage"
```

---

### Task 14: TikTok-to-LinkedIn Repurposer

**Files:**
- Create: `ugc/repurposer/__init__.py`
- Create: `ugc/repurposer/linkedin.py`
- Create: `tests/test_repurposer.py`
- Create: `.claude/commands/repurpose-linkedin.md`
- Modify: `ugc/cli.py` (add `repurpose_linkedin` method)

- [ ] **Step 1: Write failing test**

Create `ugc/repurposer/__init__.py` (empty) and `tests/test_repurposer.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\afoma\ugc-money-printer && python -m pytest tests/test_repurposer.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement ugc/repurposer/linkedin.py**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:\Users\afoma\ugc-money-printer && python -m pytest tests/test_repurposer.py -v`
Expected: 6 tests PASS

- [ ] **Step 5: Add repurpose_linkedin to CLI**

Add to `ugc/cli.py` imports:
```python
from ugc.repurposer.linkedin import LinkedInRepurposer
```

Add method to `CLI` class:
```python
    def repurpose_linkedin(self, handle: str = "", limit: int = 10) -> list:
        handle = handle or self.config.active_account
        dl = TikTokDownloader(
            output_dir=self.config.videos_dir(handle), handle=handle
        )
        videos_meta = dl._collect_metadata()
        if not videos_meta:
            logger.warning(f"No videos found for @{handle}. Run download first.")
            return []

        transcripts = {}
        for video in videos_meta[:limit]:
            vid_id = video.get("id", "")
            video_file = os.path.join(self.config.videos_dir(handle), f"{vid_id}.mp4")
            if os.path.isfile(video_file):
                try:
                    segs = self.captioner.transcribe(video_file)
                    transcripts[vid_id] = " ".join(s.word for s in segs)
                except Exception as e:
                    logger.warning(f"Transcription failed for {vid_id}: {e}")
                    transcripts[vid_id] = video.get("caption", "")
            else:
                transcripts[vid_id] = video.get("caption", "")

        profile_path = os.path.join(self.config.account_dir(handle), "style_profile.json")
        style_hints = StyleProfiler.load_profile(profile_path)

        repurposer = LinkedInRepurposer()
        posts = repurposer.batch_repurpose(
            videos_meta[:limit], transcripts, llm=self.llm, style_hints=style_hints
        )

        output_path = os.path.join(
            self.config.account_dir(handle), "linkedin_posts.json"
        )
        LinkedInRepurposer.save_posts(posts, output_path)
        logger.success(f"Generated {len(posts)} LinkedIn posts for @{handle}")
        return posts
```

- [ ] **Step 6: Create slash command**

Create `.claude/commands/repurpose-linkedin.md`:
```markdown
Convert TikTok videos into LinkedIn posts.

Usage: /repurpose-linkedin [@handle] [--limit 10]

Steps:
1. Load downloaded TikTok videos for the active account
2. Transcribe each video with WhisperX
3. Use Claude to convert each transcript into a professional LinkedIn post
4. Apply the account's style profile for tone matching
5. Save all posts to storage/accounts/{handle}/linkedin_posts.json
6. Display the generated posts for review before publishing
```

- [ ] **Step 7: Commit**

```bash
git add ugc/repurposer/__init__.py ugc/repurposer/linkedin.py tests/test_repurposer.py ugc/cli.py .claude/commands/repurpose-linkedin.md
git commit -m "feat: add TikTok-to-LinkedIn repurposer"
```
