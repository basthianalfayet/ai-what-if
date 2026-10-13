import os
import shutil
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

OUTPUT_DIR = ROOT / "output"
MUSIC_DIR = ROOT / "assets" / "music"
FONT_FILE = ROOT / "assets" / "fonts" / "PlusJakartaSans.ttf"
HISTORY_FILE = ROOT / "data" / "history.json"
SECRETS_DIR = ROOT / "secrets"

WIB = timezone(timedelta(hours=7))


def _cari_program(nama: str) -> str:
    """Cari ffmpeg/ffprobe walau PATH terminal belum diperbarui setelah instal winget."""
    ketemu = shutil.which(nama)
    if ketemu:
        return ketemu
    paket = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
    for kandidat in sorted(paket.glob(f"Gyan.FFmpeg*/*/bin/{nama}.exe"), reverse=True):
        return str(kandidat)
    raise SystemExit(f"{nama} tidak ditemukan. Pasang FFmpeg: winget install --id Gyan.FFmpeg -e --source winget")


FFMPEG = _cari_program("ffmpeg")
FFPROBE = _cari_program("ffprobe")


def _env(nama: str, default: str = "") -> str:
    return os.getenv(nama, default).strip()


GEMINI_API_KEY = _env("GEMINI_API_KEY")
GEMINI_MODEL = _env("GEMINI_MODEL", "gemini-flash-latest")
GEMINI_MODEL_CADANGAN = [
    m.strip()
    for m in _env("GEMINI_MODEL_CADANGAN", "gemini-3.8-flash,gemini-3.5-flash-lite,gemini-flash-lite-latest").split(",")
    if m.strip()
]
CHANNEL_NAME = _env("CHANNEL_NAME", "KerjaPakaiAI")
TTS_VOICE = _env("TTS_VOICE", "id-ID-ArdiNeural")
TTS_RATE = _env("TTS_RATE", "+8%")

CF_ACCOUNT_ID = _env("CF_ACCOUNT_ID")
CF_API_TOKEN = _env("CF_API_TOKEN")
def _daftar(nama: str, default: str) -> list[str]:
    return [m.strip() for m in _env(nama, default).split(",") if m.strip()]


# FLUX.2 Klein bagus dan vertikal tapi boros kuota (~1.000 neuron/gambar), jadi hanya untuk gambar hook.
# flux-1-schnell ~100 neuron/gambar untuk adegan lain yang sebagian besar tertutup kartu.
CF_IMAGE_MODELS = _daftar("CF_IMAGE_MODEL", "@cf/black-forest-labs/flux-2-klein-9b,@cf/black-forest-labs/flux-1-schnell")
CF_IMAGE_MODELS_HEMAT = _daftar("CF_IMAGE_MODEL_HEMAT", "@cf/black-forest-labs/flux-1-schnell")
IMAGE_STYLE = _env(
    "IMAGE_STYLE",
    "cinematic photo, 35mm lens, shallow depth of field, soft dramatic lighting, rich colors, "
    "Indonesian setting, vertical composition, no text, no letters, no watermark",
)

TELEGRAM_BOT_TOKEN = _env("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = _env("TELEGRAM_CHAT_ID")

YT_UPLOAD = _env("YT_UPLOAD", "0") == "1"
YT_PRIVACY = _env("YT_PRIVACY", "private")

HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

# Index mengikuti date.weekday(): 0 = Senin.
KATEGORI = [
    ("Excel & Data", "rumus Excel/Google Sheets, merapikan data berantakan, rekap, pivot, grafik"),
    ("Email & Chat Kerja", "membalas email atasan/klien, chat WhatsApp kerja, menolak dengan sopan, follow up"),
    ("Jualan Online", "caption produk, deskripsi marketplace, membalas pembeli, promo, ide konten toko"),
    ("Rapat & Laporan", "notulen rapat, laporan mingguan, ringkasan dokumen, presentasi singkat"),
    ("Cari Kerja", "CV, surat lamaran, profil LinkedIn, latihan interview, negosiasi gaji"),
    ("Belajar & Tugas", "memahami materi sulit, rangkuman, latihan soal, menyusun kerangka tulisan"),
    ("Produktivitas", "rencana harian, prioritas tugas, template kerja serbaguna, rekap prompt terbaik minggu ini"),
]

SLOT = ["pagi", "sore"]
# Video sore memakai kategori yang digeser 4 hari, jadi tidak sama dengan pagi ini maupun pagi besok.
_GESER_SLOT = {"pagi": 0, "sore": 4}


def kategori_untuk(tgl: date, slot: str = "pagi") -> tuple[str, str]:
    return KATEGORI[(tgl.weekday() + _GESER_SLOT[slot]) % 7]


def slot_berikut(tgl: date, slot: str) -> tuple[date, str]:
    return (tgl, "sore") if slot == "pagi" else (tgl + timedelta(days=1), "pagi")


def label_berikut(slot: str) -> str:
    return "nanti sore" if slot == "pagi" else "besok"


def sekarang_wib() -> datetime:
    return datetime.now(WIB)
