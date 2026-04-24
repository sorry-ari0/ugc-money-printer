Build or refresh the style profile for the active account.

Usage: /analyze-style [@handle]

1. Read the account's downloaded video metadata from storage/accounts/{handle}/videos/
2. Collect all .info.json files and parse them
3. Run StyleProfiler.build_profile() on the metadata
4. Use Claude to analyze content themes and patterns from the captions
5. Save to storage/accounts/{handle}/style_profile.json
6. Display a summary of the style profile
