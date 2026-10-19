import os
import shutil
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

OUTPUT_DIR = ROOT / "output"
MUSIC_DIR = ROOT / "assets" / "music"
FONT_FILE = ROOT / "assets" / "fonts" / "PlusJakartaSans.ttf"
# Riwayat kanal AI WHAT IF? dipisah dari history.json proyek lama.
_nama_riwayat = os.getenv("HISTORY_FILE", "data/history_whatif.json").strip() or "data/history_whatif.json"
HISTORY_FILE = Path(_nama_riwayat) if Path(_nama_riwayat).is_absolute() else ROOT / _nama_riwayat
SECRETS_DIR = ROOT / "secrets"
YT_DIR = SECRETS_DIR / "youtube_whatif"
CACHE_DIR = ROOT / "cache" / "gambar"
LOCK_DIR = ROOT / "data" / "locks"
COOLDOWN_FILE = ROOT / "data" / "cooldown.json"
KUOTA_FILE = ROOT / "data" / "kuota_gambar.json"
LEDGER_FILE = ROOT / "data" / "upload_ledger.json"
FALLBACK_AUDIO = ROOT / "assets" / "fallback" / "audio"

WIB = timezone(timedelta(hours=7))


@lru_cache(maxsize=None)
def _cari_program(nama: str) -> str:
    """Cari ffmpeg/ffprobe walau PATH terminal belum diperbarui setelah instal winget."""
    ketemu = shutil.which(nama)
    if ketemu:
        return ketemu
    paket = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
    for kandidat in sorted(paket.glob(f"Gyan.FFmpeg*/*/bin/{nama}.exe"), reverse=True):
        return str(kandidat)
    raise SystemExit(f"{nama} tidak ditemukan. Pasang FFmpeg: winget install --id Gyan.FFmpeg -e --source winget")


def ffmpeg() -> str:
    return _cari_program("ffmpeg")


def ffprobe() -> str:
    return _cari_program("ffprobe")


def _env(nama: str, default: str = "") -> str:
    return os.getenv(nama, default).strip()


GEMINI_API_KEY = _env("GEMINI_API_KEY")
GEMINI_MODEL = _env("GEMINI_MODEL", "gemini-flash-latest")
GEMINI_MODEL_CADANGAN = [
    m.strip()
    for m in _env("GEMINI_MODEL_CADANGAN", "gemini-3.8-flash,gemini-3.5-flash-lite,gemini-flash-lite-latest").split(",")
    if m.strip()
]
CHANNEL_NAME = _env("CHANNEL_NAME", "AI WHAT IF?")
TTS_VOICE = _env("TTS_VOICE", "id-ID-ArdiNeural")
TTS_RATE = _env("TTS_RATE", "+5%")

# Nama CF_* tetap yang dipakai proyek. CLOUDFLARE_* hanya alias kalau nama lama kosong.
CF_ACCOUNT_ID = _env("CF_ACCOUNT_ID") or _env("CLOUDFLARE_ACCOUNT_ID")
CF_API_TOKEN = _env("CF_API_TOKEN") or _env("CLOUDFLARE_API_TOKEN")
def _daftar(nama: str, default: str) -> list[str]:
    return [m.strip() for m in _env(nama, default).split(",") if m.strip()]


# FLUX.2 Klein bagus dan vertikal tapi boros kuota (~1.550 neuron/gambar), jadi hanya untuk gambar hook.
# flux-1-schnell ~100 neuron/gambar untuk adegan lain yang sebagian besar tertutup kartu.
CF_IMAGE_MODELS = _daftar("CF_IMAGE_MODEL", "@cf/black-forest-labs/flux-2-klein-9b,@cf/black-forest-labs/flux-1-schnell")
CF_IMAGE_MODELS_HEMAT = _daftar("CF_IMAGE_MODEL_HEMAT", "@cf/black-forest-labs/flux-1-schnell")
IMAGE_STYLE = _env(
    "IMAGE_STYLE",
    "cinematic still, anamorphic lens, shallow depth of field, dramatic natural light, rich color, "
    "vertical composition, photoreal, no text, no letters, no watermark, no logo",
)

TELEGRAM_BOT_TOKEN = _env("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = _env("TELEGRAM_CHAT_ID")

def _ya(nama: str, default: str = "false") -> bool:
    return _env(nama, default).lower() in ("1", "true", "yes", "ya")


def _angka(nama: str, default: int) -> int:
    try:
        return int(_env(nama, str(default)))
    except ValueError:
        return default


PLATFORM_MODE = _env("PLATFORM_MODE", "youtube_only").lower() or "youtube_only"
PROVIDER_MODE = _env("PROVIDER_MODE", "free_safe").lower() or "free_safe"
if PROVIDER_MODE not in ("free_safe", "auto_fallback", "local_only"):
    PROVIDER_MODE = "free_safe"

# FREE_ONLY memblokir pemanggilan berbayar sekalipun saklar fal dinyalakan.
FREE_ONLY = _ya("FREE_ONLY", "true")
PAID_FALLBACK_ENABLED = _ya("PAID_FALLBACK_ENABLED", "false")

SCRIPT_PROVIDER = _env("SCRIPT_PROVIDER", "gemini").lower() or "gemini"
SCRIPT_FALLBACK_PROVIDER = _env("SCRIPT_FALLBACK_PROVIDER", "groq").lower() or "groq"
SCRIPT_LOCAL_FALLBACK = _ya("SCRIPT_LOCAL_FALLBACK", "true")

IMAGE_PROVIDER = _env("IMAGE_PROVIDER", "cloudflare").lower() or "cloudflare"
IMAGE_FALLBACK_PROVIDER = _env("IMAGE_FALLBACK_PROVIDER", "local_assets").lower() or "local_assets"
IMAGE_LOCAL_FALLBACK = _ya("IMAGE_LOCAL_FALLBACK", "true")
IMAGE_PER_VIDEO = _angka("IMAGE_PER_VIDEO", 4)
IMAGE_DAILY_MAX = _angka("IMAGE_DAILY_MAX", 20)

TTS_PROVIDER = _env("TTS_PROVIDER", "edge_tts").lower() or "edge_tts"
TTS_FALLBACK_PROVIDER = _env("TTS_FALLBACK_PROVIDER", "local_audio").lower() or "local_audio"
TTS_FALLBACK_ENABLED = _ya("TTS_FALLBACK_ENABLED", "true")

TELEGRAM_ENABLED = _ya("TELEGRAM_ENABLED", "true")
YT_UPLOAD = _env("YT_UPLOAD", "0") == "1"
YT_PRIVACY = _env("YT_PRIVACY", "private")
if YT_PRIVACY not in ("private", "unlisted", "public"):
    YT_PRIVACY = "private"
YT_CHANNEL_NAME = _env("YT_CHANNEL_NAME", "AI WHAT IF?")

MAX_VIDEO_HARIAN = _angka("MAX_VIDEO_HARIAN", 5)
MAX_RETRY = max(1, _angka("MAX_RETRY", 2))
DURASI_MIN = _angka("DURASI_MIN", 35)
DURASI_MAX = _angka("DURASI_MAX", 55)
LOCK_DETIK = _angka("LOCK_DETIK", 3000)
# Mode uji/dry-run di-set main.py. Upload menolak selama salah satunya hidup.
MODE_UJI = False
DRY_RUN = False

# llama-3.3-70b-versatile ada di contoh resmi Groq Chat Completions.
GROQ_API_KEY = _env("GROQ_API_KEY")
GROQ_MODEL = _env("GROQ_MODEL", "llama-3.3-70b-versatile")
TEXT_FALLBACK_ENABLED = _env("TEXT_FALLBACK_ENABLED", "true").lower() in ("1", "true", "yes", "ya")

# fal-ai/flux/schnell: $0.003 per megapiksel, dibulatkan ke atas. Hanya model ini yang biayanya diketahui.
FAL_KEY = _env("FAL_KEY")
FAL_MODEL = _env("FAL_MODEL", "fal-ai/flux/schnell")
IMAGE_FALLBACK_ENABLED = _env("IMAGE_FALLBACK_ENABLED", "false").lower() in ("1", "true", "yes", "ya")
IMAGE_FALLBACK_MAX_COST_USD_PER_JOB = _env("IMAGE_FALLBACK_MAX_COST_USD_PER_JOB")

# AI Horde hanya dipakai di mode auto_fallback dan hanya kalau HORDE_ENABLED dinyalakan.
# Kuota dan antreannya tidak dijamin. Default mati supaya mode gratis tidak memanggil layanan lain.
HORDE_ENABLED = _ya("HORDE_ENABLED", "false")
HORDE_API_KEY = _env("HORDE_API_KEY", "0000000000")
HORDE_MODELS = _daftar("HORDE_MODELS", "AlbedoBase XL (SDXL),AlbedoBase XL 3.1,Juggernaut XL")
HORDE_MAX_WAIT_DETIK = int(_env("HORDE_MAX_WAIT_DETIK", "900"))
FALLBACK_DIR = ROOT / "assets" / "fallback"

HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

# Index mengikuti date.weekday(): 0 = Senin. Lima slot menggeser kategori supaya satu hari tidak bentrok.
KATEGORI = [
    ("Luar Angkasa", "tata surya, bintang, bulan, planet, dan ruang angkasa"),
    ("Bumi dan Alam", "rotasi bumi, laut, atmosfer, gunung, dan cuaca sebagai skenario fiksi"),
    ("Tubuh Manusia", "napas, tidur, darah, indera, dan batas tubuh manusia"),
    ("Hewan", "serangga, laut, rantai makanan, dan perilaku hewan"),
    ("Fisika", "gravitasi, cahaya, waktu, dan gaya fundamental"),
    ("Teknologi dan AI", "sistem otomatis, internet, dan kecerdasan buatan dalam kehidupan sehari-hari"),
    ("Masa Depan Peradaban", "kota, energi, pangan, dan cara manusia hidup bersama"),
]

JADWAL_WIB = {"pagi": "07:00", "siang": "12:00", "sore": "16:00", "malam": "19:00", "larut": "21:00"}
URUTAN_ADEGAN = ("hook", "awal", "puncak", "penutup")

SLOT = ["pagi", "siang", "sore", "malam", "larut"]
# Lima video sehari memakai lima kategori berurutan, jadi tidak bentrok dalam hari yang sama.
_GESER_SLOT = {nama: i for i, nama in enumerate(SLOT)}


def kategori_untuk(tgl: date, slot: str = "pagi") -> tuple[str, str]:
    return KATEGORI[(tgl.weekday() + _GESER_SLOT[slot]) % 7]


def slot_berikut(tgl: date, slot: str) -> tuple[date, str]:
    indeks = SLOT.index(slot)
    if indeks + 1 < len(SLOT):
        return tgl, SLOT[indeks + 1]
    return tgl + timedelta(days=1), SLOT[0]


def label_berikut(slot: str) -> str:
    return {
        "pagi": "nanti siang",
        "siang": "nanti sore",
        "sore": "nanti malam",
        "malam": "nanti larut",
        "larut": "besok",
    }[slot]


def slot_otomatis(jam: int) -> str:
    if jam < 10:
        return "pagi"
    if jam < 14:
        return "siang"
    if jam < 18:
        return "sore"
    if jam < 20:
        return "malam"
    return "larut"


def sekarang_wib() -> datetime:
    return datetime.now(WIB)
