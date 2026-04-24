import os
import tempfile
import pytest
from ugc.captioner.whisperx_captioner import WhisperXCaptioner, WordSegment


def test_format_srt_single_segment():
    segs = [WordSegment(word="Hello", start=0.0, end=0.5)]
    srt = WhisperXCaptioner.format_srt(segs)
    assert "1\n" in srt
    assert "00:00:00,000 --> 00:00:00,500" in srt
    assert "Hello" in srt


def test_format_srt_multiple_segments():
    segs = [
        WordSegment(word="Hello", start=0.0, end=0.5),
        WordSegment(word="world", start=0.6, end=1.0),
    ]
    srt = WhisperXCaptioner.format_srt(segs)
    assert "1\n" in srt
    assert "2\n" in srt


def test_format_ass_word_pop():
    segs = [
        WordSegment(word="Hello", start=0.0, end=0.5),
        WordSegment(word="world", start=0.6, end=1.0),
    ]
    ass = WhisperXCaptioner.format_ass(segs, style="word-pop")
    assert "[Script Info]" in ass
    assert "Hello" in ass
    assert "world" in ass


def test_format_ass_full_line():
    segs = [
        WordSegment(word="Hello", start=0.0, end=0.5),
        WordSegment(word="world", start=0.6, end=1.0),
    ]
    ass = WhisperXCaptioner.format_ass(segs, style="full-line")
    assert "Hello world" in ass


def test_group_words_into_lines():
    segs = [
        WordSegment(word="one", start=0.0, end=0.3),
        WordSegment(word="two", start=0.4, end=0.7),
        WordSegment(word="three", start=0.8, end=1.1),
        WordSegment(word="four", start=1.2, end=1.5),
        WordSegment(word="five", start=1.6, end=1.9),
    ]
    lines = WhisperXCaptioner.group_words(segs, max_words=3)
    assert len(lines) == 2
    assert len(lines[0]) == 3
    assert len(lines[1]) == 2
