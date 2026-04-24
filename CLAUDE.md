# UGC Money Printer

Fork of MoneyPrinterTurbo extended with a UGC creation pipeline.

## Quick Start

1. `pip install -r requirements.txt`
2. Copy `config.example.toml` to `config.toml` and fill in API keys
3. Use Claude Code commands: `/download-tiktok`, `/enhance`, `/generate`, `/scout`

## Architecture

- `app/` — Original MPT (do not modify)
- `ugc/` — UGC layer (downloader, analyzer, enhancer, captioner, publisher, scout, avatar)
- `.claude/commands/` — Claude Code slash commands
- `storage/accounts/` — Per-account data (videos, style profiles, scout data)

## Key Commands

- `/download-tiktok` — Sync TikTok videos for active account
- `/analyze-style` — Build style profile from downloaded videos
- `/enhance video.mp4` — Full pipeline: captions → b-roll → music → publish
- `/generate "topic"` — Generate video from scratch using MPT pipeline
- `/write-script "topic"` — Generate a video script in a creator's style
- `/generate-avatar` — Generate AI talking-head video via Seedance 2.0
- `/scout` — Discover viral accounts in your niche
- `/account add/use/list` — Manage TikTok accounts
- `/repurpose-linkedin` — Convert TikTok videos into LinkedIn posts
- `/publish` — Post rendered video to platforms
- `/batch` — Process folder of clips through enhance pipeline
- `/trends` — View latest trend report
- `/hooks` — Browse viral hook clips for inspiration

## Config

All UGC settings are in `config.toml` under `[ugc]`. API keys:
- `[ugc.llm]` — Anthropic API key
- `[ugc.avatar]` — fal.ai API key (Seedance 2.0)
- `[ugc.publish]` — Ayrshare API key

## Tests

```bash
python -m pytest tests/ -v
```
