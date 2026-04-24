# UGC Money Printer — Design Spec

**Date:** 2026-04-23
**Base:** MoneyPrinterTurbo fork (56.3k stars)
**Goal:** Unified UGC pipeline — record yourself, and the system handles scripting, captioning, b-roll, editing, trend scouting, and multi-platform posting, all orchestrable from Claude Code.

---

## 1. Architecture

Two pipelines share one repo:

- **Generate mode** — MPT's existing pipeline: topic → LLM script → stock footage → subtitles → rendered video
- **Enhance mode** — new UGC layer: raw talking-head clip → WhisperX captions → b-roll → music → multi-platform post

```
ugc-money-printer/
├── app/                              (original MPT — untouched)
├── webui/                            (original Streamlit UI — untouched)
├── ugc/                              (NEW — UGC layer)
│   ├── downloader/                   TikTok video downloader (yt-dlp + TTUser)
│   ├── analyzer/                     Style profiler
│   ├── enhancer/                     Footage-first pipeline
│   ├── captioner/                    WhisperX word-level captions
│   ├── publisher/                    Multi-platform posting (Ayrshare)
│   ├── scout/                        Viral discovery + trend analysis
│   └── config.py                     UGC settings loader
├── mcp/                              MCP server configs
├── .claude/                          Claude Code skills + settings
│   ├── settings.json                 MCP server wiring
│   └── commands/                     Slash commands
├── storage/                          Per-account data
│   └── accounts/
│       ├── accounts.json             Registry + active default
│       └── {handle}/
│           ├── videos/               Downloaded TikToks
│           ├── style_profile.json    Analyzed style
│           ├── metadata.json         Account info
│           ├── assets/               Extracted hooks, b-roll, audio
│           └── scouts/               Competitive intel
├── config.toml                       MPT config + [ugc] section
└── requirements.txt                  Extended with UGC deps
```

## 2. Multi-Account System

Each TikTok account gets its own directory under `storage/accounts/` with isolated style profiles, downloaded videos, and scout data. `accounts.json` tracks all registered accounts and which is currently active.

First account: `ari.from.jelly`

**Account commands:**
- `/account add @handle` — register new account, start initial download + analysis
- `/account use @handle` — switch active account
- `/account list` — show all accounts + which is active

All pipeline commands use the active account's style profile by default, overridable with `--account`.

## 3. TikTok Downloader (`ugc/downloader/`)

- `yt-dlp` + `yt-dlp-TTUser` plugin for bulk profile downloads
- Downloads to `storage/accounts/{handle}/videos/`
- Saves metadata JSON per video: caption, hashtags, views, likes, date, duration
- Incremental sync — only pulls new videos on subsequent runs
- Extracts audio tracks and thumbnail frames as reusable assets

## 4. Style Analyzer (`ugc/analyzer/`)

Runs on downloaded video library to build `style_profile.json`:

- **Pacing:** average clip duration, cut frequency, hook timing (first 1-3s)
- **Caption style:** font size, position, color, animation pattern (word-pop vs full-line)
- **Audio:** music usage %, voiceover ratio, silence patterns, trending sounds
- **Content structure:** hook → body → CTA breakdown, average segment lengths
- **Hashtag strategy:** most-used tags, tag count per post

Uses WhisperX transcription + FFmpeg scene detection + Claude for content analysis. Re-runs when new downloads arrive.

## 5. Enhance Pipeline (`ugc/enhancer/`)

Footage-first flow for raw talking-head clips:

1. **Transcribe** — WhisperX word-level timestamps
2. **Analyze** — Claude identifies hook, key points, CTA (Ollama fallback for lightweight)
3. **B-roll injection** — Pexels/Pixabay stock (MPT's sourcing), your TikTok library (topic match), Pixa MCP (AI overlays/graphics)
4. **Caption rendering** — TikTok-style word-pop (default from style_profile), full-line subtitles (YouTube option), customizable font/color/position
5. **Audio enhancement** — background music, normalization, silence trimming
6. **Format rendering** — 9:16 vertical (primary), 16:9 horizontal (secondary), 1:1 square (LinkedIn)
7. **Publishing** — Ayrshare MCP → TikTok, IG, YouTube, Twitter/X, LinkedIn

## 6. Captioner (`ugc/captioner/`)

WhisperX integration for word-level captions:

- Forced alignment via wav2vec2 for frame-perfect word timing
- Speaker diarization (pyannote) for multi-speaker content
- Output formats: SRT, ASS (styled), JSON (for programmatic use)
- Caption styles: word-pop (TikTok), karaoke highlight, full-line, minimal
- Burns into video via FFmpeg ASS filter

## 7. Publisher (`ugc/publisher/`)

Ayrshare MCP wrapper for multi-platform posting:

- Platforms: TikTok, Instagram Reels, YouTube Shorts, Twitter/X, LinkedIn
- Per-platform optimization: aspect ratio, caption length limits, hashtag formatting
- Scheduling support — post immediately or schedule for optimal times
- Post tracking — saves post IDs and links per platform

## 8. Viral Scout (`ugc/scout/`)

Competitive intelligence and trend discovery:

1. **Topic extraction** — Claude analyzes your account to identify core niches
2. **Account discovery** — searches TikTok for similar accounts with high engagement (view-to-follower ratio as viral signal)
3. **Viral post analysis** — pulls top-performing videos from discovered accounts, analyzes:
   - Hook patterns (first 1-3 seconds)
   - Caption/overlay style
   - Audio trends (trending sounds, voiceover vs music)
   - Content structure and CTA placement
   - Hashtag strategy, post timing
4. **Trend report** — actionable insights stored in `scouts/trend_report.json`
5. **Hooks library** — extracted hook clips from viral posts for inspiration

Feeds into pipelines: `/generate "topic" --trending` applies trending formats, enhance mode suggests hook improvements.

## 9. MCP Server Wiring

| Server | Purpose | Auth |
|--------|---------|------|
| ffmpeg-mcp-lite | Video processing (trim, concat, overlay, captions) | None (local) |
| Pixa MCP | AI image gen, bg removal, upscale for thumbnails | API key |
| Ayrshare MCP | Multi-platform social posting | Subscription |

Configured in `.claude/settings.json`.

## 10. LLM Routing

- **Claude** (primary): script writing, content analysis, style profiling, b-roll selection, trend analysis
- **Ollama llama-agent** (fallback): metadata tagging, caption formatting, topic classification

Config in `config.toml` under `[ugc.llm]`.

## 11. Claude Code Commands

| Command | What It Does |
|---------|-------------|
| `/download-tiktok` | Sync videos from active (or specified) TikTok account |
| `/analyze-style` | Build/refresh style_profile.json |
| `/enhance` | Raw clip → finished video (captions, b-roll, music, post) |
| `/generate` | Topic → full video (wraps MPT pipeline + style profile) |
| `/publish` | Post rendered video to selected platforms |
| `/batch` | Process folder of raw clips through enhance pipeline |
| `/account` | Add, switch, or list TikTok accounts |
| `/scout` | Discover viral accounts in your niche |
| `/trends` | Show latest trend report |
| `/hooks` | Browse extracted hooks library |

## 12. Output Formats

- **9:16 vertical** — TikTok, Instagram Reels, YouTube Shorts (primary)
- **16:9 horizontal** — YouTube long-form (secondary)
- **1:1 square** — LinkedIn, Twitter/X

## 13. Dependencies (added to requirements.txt)

```
yt-dlp
whisperx
faster-whisper
pyannote.audio
anthropic
ollama
ayrshare
```

Plus MCP servers installed via npm/pip as needed.

## 14. Config (added to config.toml)

```toml
[ugc]
active_account = "ari.from.jelly"
output_dir = "storage/output"

[ugc.llm]
primary = "anthropic"
primary_model = "claude-sonnet-4-6"
fallback = "ollama"
fallback_model = "llama-agent:latest"

[ugc.enhance]
default_caption_style = "word-pop"
default_music = true
silence_trim = true
auto_publish = false

[ugc.publish]
platforms = ["tiktok", "instagram", "youtube", "twitter", "linkedin"]

[ugc.scout]
max_accounts = 20
refresh_interval_hours = 168
```
