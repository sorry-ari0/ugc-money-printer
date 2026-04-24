import os
import subprocess
import sys
from loguru import logger


SADTALKER_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "vendor", "SadTalker",
)

SADTALKER_PYTHON = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "vendor", "sadtalker-env", "Scripts", "python.exe",
)


class SadTalkerGenerator:
    """Generate talking-head videos via SadTalker (local, CPU)."""

    def __init__(self, sadtalker_dir: str = "", python_exe: str = ""):
        self.sadtalker_dir = sadtalker_dir or SADTALKER_DIR
        self.python_exe = python_exe or SADTALKER_PYTHON
        if not os.path.isfile(self.python_exe):
            raise FileNotFoundError(
                f"SadTalker Python not found at {self.python_exe}. "
                "Run setup: py -3.10 -m venv vendor/sadtalker-env"
            )

    def generate_clip(self, source_image: str, driven_audio: str,
                      result_dir: str, still_mode: bool = True,
                      enhancer: str = "") -> str:
        os.makedirs(result_dir, exist_ok=True)

        cmd = [
            self.python_exe,
            os.path.join(self.sadtalker_dir, "inference.py"),
            "--driven_audio", driven_audio,
            "--source_image", source_image,
            "--result_dir", result_dir,
            "--cpu",
        ]

        if still_mode:
            cmd.append("--still")

        if enhancer:
            cmd.extend(["--enhancer", enhancer])

        logger.info(f"Running SadTalker (CPU mode)... this may take a few minutes")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=self.sadtalker_dir,
            timeout=600,
        )

        if result.returncode != 0:
            logger.error(f"SadTalker failed: {result.stderr[-500:]}")
            raise RuntimeError(f"SadTalker failed: {result.stderr[-500:]}")

        output_files = []
        for f in os.listdir(result_dir):
            if f.endswith(".mp4"):
                output_files.append(os.path.join(result_dir, f))
        output_files.sort(key=os.path.getmtime, reverse=True)

        if not output_files:
            raise FileNotFoundError(f"No output video found in {result_dir}")

        logger.success(f"Generated clip: {output_files[0]}")
        return output_files[0]

    def generate_from_script(self, script_sections: list, source_image: str,
                             output_dir: str) -> dict:
        """Generate clips for each script section and concatenate.

        Args:
            script_sections: list of dicts with 'label', 'text', 'audio' keys
                            (from EdgeTTSGenerator.generate_sections)
            source_image: path to reference face image
            output_dir: directory for output files
        """
        os.makedirs(output_dir, exist_ok=True)
        clip_paths = []

        for section in script_sections:
            label = section["label"]
            audio = section["audio"]
            clip_dir = os.path.join(output_dir, f"clip_{label}")

            logger.info(f"Generating clip for section: {label}")
            clip_path = self.generate_clip(
                source_image=source_image,
                driven_audio=audio,
                result_dir=clip_dir,
            )
            clip_paths.append(clip_path)

        if len(clip_paths) == 1:
            final_path = clip_paths[0]
        else:
            final_path = os.path.join(output_dir, "avatar_full.mp4")
            self._concat_clips(clip_paths, final_path)

        return {
            "video_path": final_path,
            "clips": clip_paths,
            "sections": len(script_sections),
        }

    @staticmethod
    def _concat_clips(clip_paths: list, output_path: str):
        list_file = output_path + ".txt"
        with open(list_file, "w") as f:
            for p in clip_paths:
                escaped = p.replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{escaped}'\n")
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", list_file,
            "-c", "copy",
            output_path,
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        os.remove(list_file)
        logger.info(f"Concatenated {len(clip_paths)} clips to {output_path}")
