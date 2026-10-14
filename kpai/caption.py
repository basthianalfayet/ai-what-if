from . import config
from .script_gen import Naskah

IKON = {
    "Excel & Data": "📊",
    "Email & Chat Kerja": "✉️",
    "Jualan Online": "🛍️",
    "Rapat & Laporan": "📝",
    "Cari Kerja": "💼",
    "Belajar & Tugas": "📚",
    "Produktivitas": "⚡",
}


def caption_menarik(naskah: Naskah, kategori: str) -> str:
    ikon = IKON.get(kategori, "✨")
    return (
        f"{ikon} {naskah.hook}\n\n"
        "Prompt-nya ada di video, bisa langsung kamu contek. Pause sebentar, lalu salin.\n"
        f"Biar hasilnya lebih pas, tambahin ini di akhir prompt: {naskah.trik}\n\n"
        f"{naskah.judul}\n\n"
        f"#ai #chatgpt #tipskerja #{config.CHANNEL_NAME.lower()} #fyp"
    )
