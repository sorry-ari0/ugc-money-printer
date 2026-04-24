Generate a video from a topic using MoneyPrinterTurbo's pipeline.

Usage: /generate <topic> [--trending] [--account handle]

Steps:
1. If --trending, load the active account's trend report and apply trending formats
2. Load the active account's style_profile.json for caption/pacing defaults
3. Use the MPT API to generate the video (call the FastAPI endpoint or invoke directly)
4. Apply the account's caption style
5. Output to storage/output/
