import os
import subprocess
from dataclasses import dataclass, field
from loguru import logger

ASPECT_RESOLUTIONS = {
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
    "1:1": (1080, 1080),
}


@dataclass
class EnhanceOptions:
    caption_style: str = "word-pop"
    add_music: bool = True
    add_broll: bool = True
    silence_trim: bool = True
    formats: list = field(default_factory=lambda: ["9:16"])
    platforms: list = field(default_factory=list)
    auto_publish: bool = False
    music_volume: float = 0.2
    music_path: str = ""


class EnhancePipeline:
    def __init__(self, config=None, llm=None, captioner=None, publisher=None):
        self.config = config
        self.llm = llm
        self.captioner = captioner
        self.publisher = publisher

    @staticmethod
    def _build_caption_burn_cmd(input_path: str, ass_path: str,
                                 output_path: str) -> list:
        ass_escaped = ass_path.replace("\\", "/").replace(":", "\\:")
        return [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", f"ass={ass_escaped}",
            "-c:v", "libx264", "-c:a", "aac",
            "-preset", "fast",
            output_path,
        ]

    @staticmethod
    def _build_resize_cmd(input_path: str, output_path: str,
                           aspect: str) -> list:
        w, h = ASPECT_RESOLUTIONS.get(aspect, (1080, 1920))
        return [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
                   f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black",
            "-c:v", "libx264", "-c:a", "aac",
            "-preset", "fast",
            output_path,
        ]

    @staticmethod
    def _build_music_mix_cmd(video_path: str, music_path: str,
                              output_path: str, volume: float = 0.2) -> list:
        return [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", music_path,
            "-filter_complex",
            f"[1:a]volume={volume}[bg];[0:a][bg]amix=inputs=2:duration=first[a]",
            "-map", "0:v", "-map", "[a]",
            "-c:v", "copy", "-c:a", "aac",
            output_path,
        ]

    def enhance(self, video_path: str, output_dir: str,
                options: EnhanceOptions = None) -> dict:
        if options is None:
            options = EnhanceOptions()

        os.makedirs(output_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(video_path))[0]
        results = {"source": video_path, "outputs": [], "captions": None}

        current = video_path

        if self.captioner:
            logger.info("Transcribing with WhisperX...")
            cap_result = self.captioner.transcribe_and_save(
                current, output_dir, style=options.caption_style
            )
            results["captions"] = cap_result

            captioned_path = os.path.join(output_dir, f"{base}_captioned.mp4")
            cmd = self._build_caption_burn_cmd(current, cap_result["ass"], captioned_path)
            subprocess.run(cmd, check=True, capture_output=True)
            current = captioned_path

        if options.add_music and options.music_path:
            logger.info("Mixing background music...")
            music_path = os.path.join(output_dir, f"{base}_music.mp4")
            cmd = self._build_music_mix_cmd(current, options.music_path,
                                             music_path, options.music_volume)
            subprocess.run(cmd, check=True, capture_output=True)
            current = music_path

        for aspect in options.formats:
            logger.info(f"Rendering {aspect} format...")
            suffix = aspect.replace(":", "x")
            out_path = os.path.join(output_dir, f"{base}_{suffix}.mp4")
            cmd = self._build_resize_cmd(current, out_path, aspect)
            subprocess.run(cmd, check=True, capture_output=True)
            results["outputs"].append({"aspect": aspect, "path": out_path})

        if options.auto_publish and self.publisher and options.platforms:
            logger.info("Publishing to platforms...")
            primary_output = results["outputs"][0]["path"]
            post_results = self.publisher.publish(
                primary_output, "", options.platforms
            )
            results["publish"] = post_results

        return results
