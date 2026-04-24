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
