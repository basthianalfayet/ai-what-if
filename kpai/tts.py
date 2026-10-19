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


def buat_suara(teks: str, path: Path, nama: str = "") -> tuple[list[Kata], float]:
    if not config.TTS_FALLBACK_ENABLED and not _boleh_edge():
        return _suara_lokal(teks, path, nama)
    if not _boleh_edge():
        return _suara_lokal(teks, path, nama)
    for percobaan in range(1, config.MAX_RETRY + 1):
        try:
            kata = asyncio.run(_sintesis(teks, path))
            if kata and path.exists() and path.stat().st_size > 200:
                return kata, durasi_audio(path)
            raise RuntimeError("Edge TTS tidak mengembalikan audio")
        except Exception as e:
            from .errors import Jenis, klasifikasi_exception
            salah = klasifikasi_exception("Edge TTS", e)
            if salah.jenis in (Jenis.QUOTA, Jenis.BILLING, Jenis.INVALID_KEY):
                from .mode import cooldown_kuota
                cooldown_kuota("edge_tts")
                break
            if percobaan >= config.MAX_RETRY:
                break
            print(f"  TTS gagal (percobaan {percobaan}): {salah.pesan}")
            time.sleep(min(5 * percobaan, 20))
    if config.TTS_FALLBACK_ENABLED:
        return _suara_lokal(teks, path, nama)
    raise RuntimeError("Edge TTS gagal dan audio lokal tidak diizinkan")


def _boleh_edge() -> bool:
    from .mode import boleh_suara_api, dalam_cooldown
    return boleh_suara_api() and not dalam_cooldown("edge_tts")


def _tebak_kata(teks: str, durasi: float) -> list[Kata]:
    kata = [k for k in teks.split() if k]
    if not kata:
        return []
    langkah = max(durasi, 0.2) / len(kata)
    return [Kata(k, i * langkah, (i + 1) * langkah) for i, k in enumerate(kata)]


def _suara_lokal(teks: str, path: Path, nama: str) -> tuple[list[Kata], float]:
    from .errors import NeedsReview
    kandidat = []
    if path.exists() and path.stat().st_size > 200:
        kandidat.append(path)
    if nama:
        kandidat.append(config.FALLBACK_AUDIO / f"{nama}.mp3")
        kandidat.append(config.FALLBACK_DIR / f"suara_{nama}.mp3")
    for sumber in kandidat:
        if not sumber.is_file() or sumber.stat().st_size < 200:
            continue
        if sumber != path:
            path.write_bytes(sumber.read_bytes())
        durasi = durasi_audio(path)
        print(f"  Suara {nama or path.stem}: audio lokal")
        return _tebak_kata(teks, durasi), durasi
    raise NeedsReview(f"Audio untuk {nama or 'adegan'} tidak tersedia. Video ditandai untuk ditinjau.")
