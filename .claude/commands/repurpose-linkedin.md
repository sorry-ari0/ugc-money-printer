Convert TikTok videos into LinkedIn posts.

Usage: /repurpose-linkedin [@handle] [--limit 10]

Steps:
1. Load downloaded TikTok videos for the active account
2. Transcribe each video with WhisperX
3. Use Claude to convert each transcript into a professional LinkedIn post
4. Apply the account's style profile for tone matching
5. Save all posts to storage/accounts/{handle}/linkedin_posts.json
6. Display the generated posts for review before publishing
