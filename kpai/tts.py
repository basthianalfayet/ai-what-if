import asyncio
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

import edge_tts

from . import config


@dataclass
class Kata:
    teks: str
    mulai: float
    selesai: float


async def _sintesis(teks: str, path: Path) -> list[Kata]:
    comm = edge_tts.Communicate(teks, config.TTS_VOICE, rate=config.TTS_RATE, boundary="WordBoundary")
    kata = []
    with open(path, "wb") as f:
        async for ch in comm.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                mulai = ch["offset"] / 1e7
                kata.append(Kata(ch["text"], mulai, mulai + ch["duration"] / 1e7))
    return kata


def durasi_audio(path: Path) -> float:
    out = subprocess.run(
        [config.ffprobe(), "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def buat_suara(teks: str, path: Path) -> tuple[list[Kata], float]:
    for percobaan in range(1, 4):
        try:
            kata = asyncio.run(_sintesis(teks, path))
            if kata:
                return kata, durasi_audio(path)
            raise RuntimeError("Edge TTS tidak mengembalikan timing kata")
        except Exception as e:
            if percobaan == 3:
                raise
            print(f"  TTS gagal (percobaan {percobaan}): {e}")
            time.sleep(5 * percobaan)
