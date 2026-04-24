import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from loguru import logger

try:
    import fal_client
except ImportError:
    fal_client = None

try:
    import requests as _requests
except ImportError:
    _requests = None


MODELS = {
    "text-to-video": "bytedance/seedance-2.0/text-to-video",
    "image-to-video": "bytedance/seedance-2.0/image-to-video",
    "reference-to-video": "bytedance/seedance-2.0/reference-to-video",
    "fast-text-to-video": "bytedance/seedance-2.0/fast/text-to-video",
    "fast-image-to-video": "bytedance/seedance-2.0/fast/image-to-video",
    "fast-reference-to-video": "bytedance/seedance-2.0/fast/reference-to-video",
}

MAX_CLIP_SECONDS = 15


@dataclass
class SeedanceOptions:
    resolution: str = "720p"
    duration: str = "auto"
    aspect_ratio: str = "9:16"
    generate_audio: bool = True
    seed: int = -1
    fast: bool = False


class SeedanceAvatar:
    """Generate talking-head videos via fal.ai's Seedance 2.0 API."""

    def __init__(self, fal_key: str = ""):
        if fal_client is None:
            raise ImportError("fal-client not installed. Install: pip install fal-client")
        if fal_key:
            os.environ["FAL_KEY"] = fal_key

    def _pick_model(self, mode: str, fast: bool = False) -> str:
        key = f"fast-{mode}" if fast else mode
        model = MODELS.get(key)
        if not model:
            raise ValueError(f"Unknown mode: {mode}. Choose from: text-to-video, image-to-video, reference-to-video")
        return model

    def generate_clip(self, prompt: str, opts: SeedanceOptions = None,
                      image_url: str = "", reference_image_url: str = "") -> dict:
        if opts is None:
            opts = SeedanceOptions()

        if image_url:
            mode = "image-to-video"
        elif reference_image_url:
            mode = "reference-to-video"
        else:
            mode = "text-to-video"

        model_id = self._pick_model(mode, opts.fast)

        args = {
            "prompt": prompt,
            "resolution": opts.resolution,
            "duration": opts.duration,
            "aspect_ratio": opts.aspect_ratio,
            "generate_audio": opts.generate_audio,
        }
        if opts.seed >= 0:
            args["seed"] = opts.seed
        if image_url:
            args["image_url"] = image_url
        if reference_image_url:
            args["image_url"] = reference_image_url

        logger.info(f"Generating clip via {model_id}...")

        def on_queue_update(update):
            if hasattr(update, "logs") and update.logs:
                for log in update.logs:
                    logger.debug(f"[seedance] {log.get('message', log)}")

        result = fal_client.subscribe(model_id, arguments=args, with_logs=True,
                                      on_queue_update=on_queue_update)

        video_info = result.get("video", {})
        logger.success(f"Clip generated: {video_info.get('url', 'no url')}")
        return {
            "video_url": video_info.get("url", ""),
            "content_type": video_info.get("content_type", "video/mp4"),
            "file_size": video_info.get("file_size", 0),
            "seed": result.get("seed"),
            "model": model_id,
        }

    def download_clip(self, video_url: str, output_path: str) -> str:
        if _requests is None:
            raise ImportError("requests not installed")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        resp = _requests.get(video_url, stream=True, timeout=120)
        resp.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"Downloaded clip to {output_path}")
        return output_path

    def extract_reference_frame(self, video_path: str, output_path: str = "",
                                timestamp: float = 1.0) -> str:
        if not output_path:
            base = os.path.splitext(video_path)[0]
            output_path = f"{base}_frame.png"
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(timestamp),
            "-i", video_path,
            "-frames:v", "1",
            "-q:v", "2",
            output_path,
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info(f"Extracted reference frame to {output_path}")
        return output_path

    def generate_avatar_video(self, script: dict, reference_image_url: str,
                              output_dir: str, opts: SeedanceOptions = None) -> dict:
        """Generate a full avatar video from a script dict.

        Generates one clip per script section (hook + body + cta), then
        concatenates them with ffmpeg.
        """
        if opts is None:
            opts = SeedanceOptions()

        os.makedirs(output_dir, exist_ok=True)

        sections = []
        sections.append(("hook", script.get("hook", "")))
        for i, body in enumerate(script.get("body", []), 1):
            sections.append((f"body_{i}", body))
        sections.append(("cta", script.get("cta", "")))

        clip_paths = []
        for label, text in sections:
            if not text:
                continue
            prompt = (
                f"A person speaking directly to camera in a TikTok-style vertical video. "
                f"Natural lighting, casual setting. They are saying: \"{text}\""
            )

            result = self.generate_clip(
                prompt=prompt, opts=opts,
                reference_image_url=reference_image_url,
            )

            clip_path = os.path.join(output_dir, f"clip_{label}.mp4")
            self.download_clip(result["video_url"], clip_path)
            clip_paths.append(clip_path)

        if not clip_paths:
            return {"error": "No clips generated"}

        if len(clip_paths) == 1:
            final_path = clip_paths[0]
        else:
            final_path = os.path.join(output_dir, "avatar_raw.mp4")
            self._concat_clips(clip_paths, final_path)

        return {
            "video_path": final_path,
            "clips": clip_paths,
            "sections": len(sections),
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
