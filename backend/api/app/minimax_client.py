from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from app.config import settings


class MinimaxClientError(RuntimeError):
    pass


def _mock_seed(*parts: str) -> int:
    h = hashlib.sha256("::".join(parts).encode("utf-8")).hexdigest()
    return int(h[:8], 16)


def minimax_llm_generate_concepts(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Required function.
    Input: prompt pack / topic / constraints.
    Output: structured JSON with concept cards, reel scripts, quiz items.
    """
    if settings.minimax_mock:
        topic = str(payload.get("topic_title") or payload.get("topic") or "Topic")
        seed = _mock_seed("llm", topic, json.dumps(payload, sort_keys=True, default=str))
        concept_cards = [
            {
                "title": f"{topic}: Core idea #{(seed % 3) + 1}",
                "definition": f"A short definition for {topic}.",
                "example": f"An example application of {topic}.",
                "check_for_understanding": f"What is the key intuition behind {topic}?",
            }
        ]
        reel_script = {
            "hook": f"Stop scrolling—learn {topic} in 30 seconds.",
            "steps": [
                f"Define {topic} in one sentence.",
                f"Show a quick example for {topic}.",
                "End with a one-line recap.",
            ],
            "cta": "Save this and try the quiz.",
        }
        quiz_item = {
            "question": f"Which statement best describes {topic}?",
            "choices": [
                f"It is a key concept in {topic}.",
                "It is unrelated trivia.",
                "It is always false.",
                "It only applies in rare cases.",
            ],
            "answer_index": 0,
            "explanation": f"{topic} is introduced as a core concept.",
        }
        return {"concept_cards": concept_cards, "reel_script": reel_script, "quiz_items": [quiz_item]}

    if not settings.minimax_api_key:
        raise MinimaxClientError("MINIMAX_API_KEY is not configured")

    # Placeholder for real MiniMax LLM call.
    # Implement according to MiniMax docs for your chosen model.
    try:
        with httpx.Client(base_url=settings.minimax_base_url, timeout=60.0) as client:
            resp = client.post(
                "/v1/llm/generate",
                headers={"Authorization": f"Bearer {settings.minimax_api_key}"},
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        raise MinimaxClientError(f"MiniMax LLM call failed: {e}") from e


def minimax_tts_generate_voice(script: str, voice_style: str) -> str:
    """
    Required function.
    Output: path to an audio file.
    """
    if settings.minimax_mock:
        fd, path = tempfile.mkstemp(prefix="doomlearn_tts_", suffix=".wav")
        os.close(fd)
        # Generate 1s of silence so downstream muxing works.
        with wave.open(path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(22050)
            wf.writeframes(b"\x00\x00" * 22050)
        return path

    if not settings.minimax_api_key:
        raise MinimaxClientError("MINIMAX_API_KEY is not configured")

    # Placeholder for real MiniMax TTS call.
    raise MinimaxClientError("MiniMax TTS real call not implemented (use MINIMAX_MOCK=1 for dev)")


def minimax_music_generate(mood: str, duration: int) -> str:
    """
    Required function (optional use).
    Output: path to a music track file.
    """
    if settings.minimax_mock:
        fd, path = tempfile.mkstemp(prefix="doomlearn_music_", suffix=".wav")
        os.close(fd)
        with wave.open(path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(22050)
            wf.writeframes(b"\x00\x00" * 22050)  # placeholder
        return path

    if not settings.minimax_api_key:
        raise MinimaxClientError("MINIMAX_API_KEY is not configured")

    raise MinimaxClientError("MiniMax music real call not implemented (use MINIMAX_MOCK=1 for dev)")


def minimax_video_generate(prompt: str, assets: dict[str, Any] | None = None) -> str:
    """
    Required function.
    Output: path to a generated video segment (vertical).
    """
    if settings.minimax_mock:
        out = Path(tempfile.mkdtemp(prefix="doomlearn_video_")) / "segment.mp4"
        duration = int((assets or {}).get("duration_sec") or 3)
        _ffmpeg_generate_color_video(str(out), duration=duration)
        return str(out)

    if not settings.minimax_api_key:
        raise MinimaxClientError("MINIMAX_API_KEY is not configured")

    # Placeholder for real MiniMax video generation call.
    raise MinimaxClientError("MiniMax video real call not implemented (use MINIMAX_MOCK=1 for dev)")


def _ffmpeg_generate_color_video(path: str, duration: int = 3) -> None:
    """
    Minimal FFmpeg generator: creates a 1080x1920 mp4 with silent audio.
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=black:s=1080x1920:d={duration}",
        "-f",
        "lavfi",
        "-i",
        f"anullsrc=r=44100:cl=mono",
        "-shortest",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        path,
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError as e:
        raise MinimaxClientError("ffmpeg not found; install ffmpeg or keep MINIMAX_MOCK=1") from e
    except subprocess.CalledProcessError as e:
        raise MinimaxClientError(f"ffmpeg failed: {e}") from e

