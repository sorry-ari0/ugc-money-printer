import os
from dataclasses import dataclass
from typing import Optional
from loguru import logger


@dataclass
class WordSegment:
    word: str
    start: float
    end: float


class WhisperXCaptioner:
    def __init__(self, model_size: str = "large-v3", device: str = "cpu"):
        self.model_size = model_size
        self.device = device

    def transcribe(self, audio_path: str) -> list:
        try:
            import whisperx
        except ImportError:
            logger.error("whisperx not installed. Install: pip install whisperx")
            raise

        model = whisperx.load_model(self.model_size, self.device)
        audio = whisperx.load_audio(audio_path)
        result = model.transcribe(audio, batch_size=16)

        align_model, metadata = whisperx.load_align_model(
            language_code=result["language"], device=self.device
        )
        aligned = whisperx.align(
            result["segments"], align_model, metadata, audio, self.device
        )

        words = []
        for seg in aligned["word_segments"]:
            words.append(WordSegment(
                word=seg["word"],
                start=seg["start"],
                end=seg["end"],
            ))
        return words

    @staticmethod
    def group_words(segments: list, max_words: int = 4) -> list:
        lines = []
        current = []
        for seg in segments:
            current.append(seg)
            if len(current) >= max_words:
                lines.append(current)
                current = []
        if current:
            lines.append(current)
        return lines

    @staticmethod
    def _ts(seconds: float, fmt: str = "srt") -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        if fmt == "srt":
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
        cs = int((seconds % 1) * 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    @staticmethod
    def format_srt(segments: list) -> str:
        lines = []
        for i, seg in enumerate(segments, 1):
            start = WhisperXCaptioner._ts(seg.start, "srt")
            end = WhisperXCaptioner._ts(seg.end, "srt")
            lines.append(f"{i}\n{start} --> {end}\n{seg.word}\n")
        return "\n".join(lines)

    @staticmethod
    def format_ass(segments: list, style: str = "word-pop",
                   font: str = "Arial", font_size: int = 48,
                   primary_color: str = "&H00FFFFFF",
                   outline_color: str = "&H00000000") -> str:
        header = (
            "[Script Info]\n"
            "Title: UGC Captions\n"
            "ScriptType: v4.00+\n"
            "PlayResX: 1080\n"
            "PlayResY: 1920\n\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
            "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
            "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
            "Alignment, MarginL, MarginR, MarginV, Encoding\n"
            f"Style: Default,{font},{font_size},{primary_color},&H000000FF,"
            f"{outline_color},&H80000000,-1,0,0,0,100,100,0,0,1,3,0,2,40,40,200,1\n\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        )

        events = []
        ts = WhisperXCaptioner._ts

        if style == "word-pop":
            for seg in segments:
                start = ts(seg.start, "ass")
                end = ts(seg.end, "ass")
                text = r"{\fscx120\fscy120}" + seg.word
                events.append(
                    f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}"
                )
        elif style == "full-line":
            groups = WhisperXCaptioner.group_words(segments, max_words=6)
            for group in groups:
                start = ts(group[0].start, "ass")
                end = ts(group[-1].end, "ass")
                text = " ".join(s.word for s in group)
                events.append(
                    f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}"
                )
        elif style == "karaoke":
            groups = WhisperXCaptioner.group_words(segments, max_words=6)
            for group in groups:
                start = ts(group[0].start, "ass")
                end = ts(group[-1].end, "ass")
                parts = []
                for s in group:
                    dur_cs = int((s.end - s.start) * 100)
                    parts.append(r"{\kf" + str(dur_cs) + "}" + s.word)
                events.append(
                    f"Dialogue: 0,{start},{end},Default,,0,0,0,,{' '.join(parts)}"
                )
        else:
            for seg in segments:
                start = ts(seg.start, "ass")
                end = ts(seg.end, "ass")
                events.append(
                    f"Dialogue: 0,{start},{end},Default,,0,0,0,,{seg.word}"
                )

        return header + "\n".join(events) + "\n"

    def transcribe_and_save(self, video_path: str, output_dir: str,
                            style: str = "word-pop") -> dict:
        segments = self.transcribe(video_path)
        base = os.path.splitext(os.path.basename(video_path))[0]
        os.makedirs(output_dir, exist_ok=True)

        srt_path = os.path.join(output_dir, f"{base}.srt")
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(self.format_srt(segments))

        ass_path = os.path.join(output_dir, f"{base}.ass")
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(self.format_ass(segments, style=style))

        transcript = " ".join(s.word for s in segments)
        return {"srt": srt_path, "ass": ass_path, "transcript": transcript}
