"""Pemeriksaan sebelum upload. Gagal pemeriksaan tidak boleh tayang otomatis."""

from pathlib import Path

from . import config
from .topik import mirip_dengan_daftar

_KLAIM = (
    "kamu tidak akan percaya",
    "rahasia yang disembunyikan",
    "ilmuwan bungkam",
    "100% pasti",
    "pasti terjadi besok",
    "ini benar-benar terjadi",
    "fakta bahwa ini sudah terjadi",
)


def masalah_naskah(naskah) -> list[str]:
    masalah = []
    if not (naskah.topik or "").strip() or not (naskah.hook or "").strip():
        masalah.append("naskah atau hook kosong")
    if len(getattr(naskah, "adegan", []) or []) < 1:
        masalah.append("tidak ada adegan")
    for adegan in getattr(naskah, "adegan", []) or []:
        if not (adegan.narasi or "").strip():
            masalah.append(f"narasi {adegan.id} kosong")
        if not (adegan.prompt_gambar or "").strip():
            masalah.append(f"prompt gambar {adegan.id} kosong")
    if not (naskah.ending or "").strip():
        masalah.append("ending kosong")
    if not (naskah.penjelasan_ilmiah or "").strip() or not (naskah.batas_ketidakpastian or "").strip():
        masalah.append("penjelasan atau batas ketidakpastian kosong")
    gabungan = " ".join(
        [
            naskah.hook,
            naskah.ending,
            naskah.judul_youtube,
            " ".join(a.narasi for a in naskah.adegan),
        ]
    ).lower()
    for frasa in _KLAIM:
        if frasa in gabungan:
            masalah.append(f"klaim berlebihan: {frasa}")
    if not naskah.pengungkapan_sintetis:
        masalah.append("pengungkapan konten sintetis belum diaktifkan")
    if getattr(naskah, "perlu_tinjauan", False):
        masalah.append("naskah ditandai perlu ditinjau")
    return masalah


def masalah_duplikat(naskah, riwayat_topik: list[str]) -> list[str]:
    lama = mirip_dengan_daftar(naskah.topik, naskah.inti, riwayat_topik)
    if not lama:
        return []
    return [f"topik terlalu mirip dengan '{lama}'"]


def nilai_probe(info: dict) -> list[str]:
    masalah = []
    aliran = info.get("streams") or []
    video = next((s for s in aliran if s.get("codec_type") == "video"), None)
    audio = next((s for s in aliran if s.get("codec_type") == "audio"), None)
    if video is None:
        masalah.append("stream video tidak ada")
    else:
        if video.get("codec_name") not in (None, "h264"):
            masalah.append(f"codec video {video.get('codec_name')} bukan h264")
        try:
            lebar, tinggi = int(video.get("width") or 0), int(video.get("height") or 0)
        except (TypeError, ValueError):
            lebar, tinggi = 0, 0
        if lebar < 2 or tinggi < 2 or abs((lebar / tinggi) - (9 / 16)) > 0.02:
            masalah.append(f"rasio {lebar}x{tinggi} bukan 9:16")
    if audio is None:
        masalah.append("stream audio tidak ada")
    elif audio.get("codec_name") not in (None, "aac"):
        masalah.append(f"codec audio {audio.get('codec_name')} bukan aac")
    try:
        durasi = float((info.get("format") or {}).get("duration") or 0)
    except (TypeError, ValueError):
        durasi = 0
    if durasi < config.DURASI_MIN or durasi > config.DURASI_MAX:
        masalah.append(f"durasi {durasi:.1f} detik di luar {config.DURASI_MIN}-{config.DURASI_MAX}")
    return masalah


def periksa_berkas(path: Path) -> list[str]:
    if not path.is_file() or path.stat().st_size < 1000:
        return ["file video kosong atau tidak ada"]
    import json
    import subprocess
    try:
        hasil = subprocess.run(
            [config.ffprobe(), "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
            capture_output=True, text=True, check=True,
        )
        info = json.loads(hasil.stdout or "{}")
    except Exception as e:
        return [f"video tidak bisa dibaca: {e}"]
    return nilai_probe(info)


def unggah_diizinkan(*, uji: bool, dry_run: bool, yt_upload: bool, kualitas_lolos: bool, sudah_unggah: bool, platform: str) -> bool:
    if uji or dry_run or config.MODE_UJI or config.DRY_RUN:
        return False
    if not yt_upload or not kualitas_lolos or sudah_unggah:
        return False
    if platform != "youtube":
        return False
    return config.PLATFORM_MODE == "youtube_only"
