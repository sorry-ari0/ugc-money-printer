Publish a rendered video to social platforms.

Usage: /publish <video_path> [--platforms tiktok,instagram,youtube,twitter,linkedin] [--caption "text"] [--schedule "2026-04-24T10:00:00Z"]

Steps:
1. Read config.toml for Ayrshare API key and default platforms
2. If no caption provided, generate one with Claude based on the video
3. Publish via AyrsharePublisher
4. Save post results to storage/output/posts/
