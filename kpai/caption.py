from . import config
from .script_gen import Naskah


def _bersih_judul(teks: str) -> str:
    judul = " ".join((teks or "").split())
    if len(judul) <= 100:
        return judul
    potong = judul[:99].rsplit(" ", 1)[0]
    return potong if potong else judul[:99]


_EMOJI = {
    "luar angkasa": "🪐",
    "bumi dan alam": "🌍",
    "tubuh manusia": "🧠",
    "hewan": "🐾",
    "fisika": "⚡",
    "teknologi dan ai": "🤖",
    "masa depan peradaban": "🏙️",
}


def _emoji(kategori: str) -> str:
    return _EMOJI.get((kategori or "").casefold().strip(), "🤔")


def judul_youtube(naskah: Naskah, kategori: str) -> str:
    judul = _bersih_judul(naskah.judul_youtube or naskah.judul_kerja or naskah.hook)
    emoji = _emoji(kategori)
    if judul.startswith(emoji):
        return judul
    gabungan = f"{emoji} {judul}"
    if len(gabungan) <= 100:
        return gabungan
    return judul


# Tiga tag pertama yang muncul di atas judul Shorts. Sisanya tetap di deskripsi.
_TAGAR_TETAP = (
    "#Shorts",
    "#WhatIf",
    "#FaktaUnik",
    "#Viral",
    "#TahukahKamu",
    "#Sains",
    "#Edukasi",
    "#AIWhatIf",
    "#FiksiIlmiah",
)


def _jadi_tagar(teks: str) -> str:
    potongan = [bagian for bagian in str(teks).replace("#", " ").split() if bagian]
    if not potongan:
        return ""
    return "#" + "".join(bagian[:1].upper() + bagian[1:] for bagian in potongan)


def tagar_youtube(kategori: str, naskah: Naskah | None = None) -> list[str]:
    dasar = list(_TAGAR_TETAP)
    if kategori:
        dasar.append(_jadi_tagar(kategori))
    if naskah is not None:
        for item in naskah.hashtag or []:
            tag = _jadi_tagar(item)
            if tag:
                dasar.append(tag)
    hasil = []
    sudah = set()
    for item in dasar:
        kunci = item.casefold()
        if item and kunci not in sudah:
            sudah.add(kunci)
            hasil.append(item)
    return hasil[:15]


def tag_youtube(naskah: Naskah, kategori: str) -> list[str]:
    dasar = ["shorts", "what if", "ai what if", "sains", kategori.lower(), config.CHANNEL_NAME.lower()]
    hasil = []
    for teks in [*(naskah.hashtag or []), *(getattr(naskah, "tags", None) or []), *dasar]:
        item = str(teks).strip().lower().lstrip("#")
        if item and item not in hasil:
            hasil.append(item)
    return hasil[:12]


def deskripsi_youtube(naskah: Naskah, kategori: str) -> str:
    emoji = _emoji(kategori)
    baris = [
        " ".join(tagar_youtube(kategori, naskah)),
        "",
        f"{emoji} {naskah.hook.strip()}",
        "",
        naskah.deskripsi_youtube.strip(),
        "",
        "Yang masuk akal:",
        naskah.penjelasan_ilmiah.strip(),
        "",
        "Yang jangan dianggap pasti:",
        naskah.batas_ketidakpastian.strip(),
    ]
    if naskah.pertanyaan_komentar.strip():
        baris += ["", f"💬 {naskah.pertanyaan_komentar.strip()}", "Tulis jawabanmu di komentar."]
    if naskah.referensi:
        baris += ["", "Catatan sumber:"]
        baris += [f"- {item}" for item in naskah.referensi]
    if naskah.pengungkapan_sintetis:
        baris += [
            "",
            "Video ini memakai narasi dan gambar bantuan AI untuk skenario fiksi. Ini bukan rekaman kejadian nyata.",
        ]
    return "\n".join(baris)


def caption_menarik(naskah: Naskah, kategori: str) -> str:
    emoji = _emoji(kategori)
    return (
        f"{emoji} {naskah.hook.strip()}\n\n"
        f"💬 {naskah.pertanyaan_komentar.strip()}\n\n"
        f"{' '.join(tagar_youtube(kategori, naskah))}"
    )


def simpan_metadata(folder, naskah: Naskah, kategori: str) -> None:
    judul = judul_youtube(naskah, kategori)
    deskripsi = deskripsi_youtube(naskah, kategori)
    (folder / "youtube.txt").write_text(f"{judul}\n\n{deskripsi}\n", encoding="utf-8")
    if config.PLATFORM_MODE != "youtube_only":
        (folder / "caption_tiktok.txt").write_text(caption_menarik(naskah, kategori) + "\n", encoding="utf-8")
