import os
import subprocess
from loguru import logger


class EdgeTTSGenerator:
    """Generate speech audio using Microsoft Edge TTS (free, unlimited)."""

    DEFAULT_VOICE = "en-US-GuyNeural"

    def __init__(self, voice: str = ""):
        self.voice = voice or self.DEFAULT_VOICE

    def generate(self, text: str, output_path: str, voice: str = "") -> str:
        voice = voice or self.voice
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        cmd = [
            "python", "-m", "edge_tts",
            "--voice", voice,
            "--text", text,
            "--write-media", output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Edge TTS failed: {result.stderr}")
            raise RuntimeError(f"Edge TTS failed: {result.stderr}")
        logger.info(f"Generated TTS audio: {output_path}")
        return output_path

    def generate_sections(self, script: dict, output_dir: str,
                          voice: str = "") -> list:
        """Generate audio for each section of a script dict."""
        os.makedirs(output_dir, exist_ok=True)
        sections = []

        hook = script.get("hook", "")
        if hook:
            path = os.path.join(output_dir, "hook.mp3")
            self.generate(hook, path, voice)
            sections.append({"label": "hook", "text": hook, "audio": path})

        for i, body in enumerate(script.get("body", []), 1):
            path = os.path.join(output_dir, f"body_{i}.mp3")
            self.generate(body, path, voice)
            sections.append({"label": f"body_{i}", "text": body, "audio": path})

        cta = script.get("cta", "")
        if cta:
            path = os.path.join(output_dir, "cta.mp3")
            self.generate(cta, path, voice)
            sections.append({"label": "cta", "text": cta, "audio": path})

        logger.success(f"Generated {len(sections)} audio sections")
        return sections
