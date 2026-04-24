Write a video script based on a creator's style.

Usage: /write-script "topic or detailed prompt" [@handle] [--duration 60]

Steps:
1. Load the style profile for the specified account (or active account)
2. Use Claude to generate a structured video script matching the creator's style
3. Output: hook, body sections, CTA, b-roll suggestions, hashtags
4. Save to storage/accounts/{handle}/scripts/
5. Display teleprompter-formatted script for review
