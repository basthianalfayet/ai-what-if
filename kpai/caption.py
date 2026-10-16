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


TAGAR_KATEGORI = {
    "Excel & Data": ["#Excel", "#GoogleSheets", "#RumusExcel"],
    "Email & Chat Kerja": ["#EmailKerja", "#KerjaKantor"],
    "Jualan Online": ["#JualanOnline", "#Olshop"],
    "Rapat & Laporan": ["#LaporanKerja", "#Rapat"],
    "Cari Kerja": ["#CariKerja", "#CV", "#LamaranKerja"],
    "Belajar & Tugas": ["#Belajar", "#TugasKuliah"],
    "Produktivitas": ["#Produktivitas", "#KerjaLebihCepat"],
}


def _ikon(kategori: str) -> str:
    return IKON.get(kategori, "✨")


def caption_menarik(naskah: Naskah, kategori: str) -> str:
    return (
        f"{_ikon(kategori)} {naskah.hook}\n\n"
        "Prompt-nya ada di video, bisa langsung kamu contek. Pause sebentar, lalu salin.\n"
        f"Biar hasilnya lebih pas, tambahin ini di akhir prompt: {naskah.trik}\n\n"
        f"{naskah.judul}\n\n"
        f"#ai #chatgpt #tipskerja #{config.CHANNEL_NAME.lower()} #fyp"
    )


def judul_youtube(naskah: Naskah, kategori: str) -> str:
    """Judul Shorts = hook. Itu kalimat yang kebaca sebelum orang scroll."""
    hook = " ".join(naskah.hook.split())
    judul = f"{_ikon(kategori)} {hook}"
    if len(judul) <= 100:
        return judul
    if len(hook) <= 100:
        return hook
    potong = hook[:99].rsplit(" ", 1)[0]
    return potong if potong else hook[:99]


def tagar_youtube(kategori: str) -> list[str]:
    tagar = ["#Shorts", "#AI", "#ChatGPT", "#PromptAI", "#TipsKerja", f"#{config.CHANNEL_NAME}"]
    for item in TAGAR_KATEGORI.get(kategori, []):
        if item not in tagar:
            tagar.append(item)
    return tagar[:15]


def tag_youtube(naskah: Naskah, kategori: str) -> list[str]:
    dasar = ["shorts", "ai", "chatgpt", "prompt ai", "tips kerja", config.CHANNEL_NAME.lower(), kategori.lower()]
    hasil = []
    for teks in [*naskah.tags, *dasar]:
        item = teks.strip().lower().lstrip("#")
        if item and item not in hasil:
            hasil.append(item)
    return hasil[:12]


def deskripsi_youtube(naskah: Naskah, kategori: str) -> str:
    return (
        f"{_ikon(kategori)} {naskah.hook.strip()}\n\n"
        f"{naskah.deskripsi.strip()}\n\n"
        "Prompt lengkapnya ada di video. Pause sebentar, lalu contek.\n\n"
        f"Prompt:\n{naskah.prompt.strip()}\n\n"
        f"Trik biar hasilnya lebih kena:\n{naskah.trik.strip()}\n\n"
        "Simpan Shorts ini. Nanti pas lagi butuh, tinggal buka, jangan tulis prompt dari nol.\n\n"
        + " ".join(tagar_youtube(kategori))
    )
