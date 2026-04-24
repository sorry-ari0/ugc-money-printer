Generate an AI avatar video from a script using Seedance 2.0.

Usage: /generate-avatar [script.json] [@handle] [--reference-url "https://..."] [--fast]

Steps:
1. Load the script (from path or most recent in storage/accounts/{handle}/scripts/)
2. Extract a reference frame from a downloaded TikTok video (or use provided URL)
3. Generate talking-head clips for each script section via Seedance 2.0 (fal.ai)
4. Concatenate clips into a single video with ffmpeg
5. Save raw avatar video to storage/accounts/{handle}/avatar_output/
6. Optionally run through /enhance for captions, b-roll, and music
