from . import config
from .script_gen import Naskah


def _bersih_judul(teks: str) -> str:
    judul = " ".join((teks or "").split())
    if len(judul) <= 100:
        return judul
    potong = judul[:99].rsplit(" ", 1)[0]
    return potong if potong else judul[:99]


def judul_youtube(naskah: Naskah, kategori: str) -> str:
    del kategori
    return _bersih_judul(naskah.judul_youtube or naskah.judul_kerja or naskah.hook)


def tagar_youtube(kategori: str) -> list[str]:
    dasar = ["#Shorts", "#WhatIf", "#AIWhatIf", "#Sains", "#FiksiIlmiah"]
    if kategori:
        dasar.append("#" + "".join(kategori.split()))
    hasil = []
    for item in dasar:
        if item not in hasil:
            hasil.append(item)
    return hasil[:8]


def tag_youtube(naskah: Naskah, kategori: str) -> list[str]:
    dasar = ["shorts", "what if", "ai what if", "sains", kategori.lower(), config.CHANNEL_NAME.lower()]
    hasil = []
    for teks in [*(naskah.hashtag or []), *(getattr(naskah, "tags", None) or []), *dasar]:
        item = str(teks).strip().lower().lstrip("#")
        if item and item not in hasil:
            hasil.append(item)
    return hasil[:12]


def deskripsi_youtube(naskah: Naskah, kategori: str) -> str:
    baris = [
        naskah.hook.strip(),
        "",
        naskah.deskripsi_youtube.strip(),
        "",
        "Yang cukup kita ketahui:",
        naskah.penjelasan_ilmiah.strip(),
        "",
        "Yang tidak boleh dianggap pasti:",
        naskah.batas_ketidakpastian.strip(),
    ]
    if naskah.pertanyaan_komentar.strip():
        baris += ["", naskah.pertanyaan_komentar.strip()]
    if naskah.referensi:
        baris += ["", "Catatan sumber:"]
        baris += [f"- {item}" for item in naskah.referensi]
    if naskah.pengungkapan_sintetis:
        baris += [
            "",
            "Video ini memakai narasi dan gambar bantuan AI untuk skenario fiksi. Ini bukan rekaman kejadian nyata.",
        ]
    baris += ["", " ".join(tagar_youtube(kategori))]
    return "\n".join(baris)


def caption_menarik(naskah: Naskah, kategori: str) -> str:
    return (
        f"{naskah.hook.strip()}\n\n"
        f"{naskah.pertanyaan_komentar.strip()}\n\n"
        f"{judul_youtube(naskah, kategori)}"
    )


def simpan_metadata(folder, naskah: Naskah, kategori: str) -> None:
    judul = judul_youtube(naskah, kategori)
    deskripsi = deskripsi_youtube(naskah, kategori)
    (folder / "youtube.txt").write_text(f"{judul}\n\n{deskripsi}\n", encoding="utf-8")
    if config.PLATFORM_MODE != "youtube_only":
        (folder / "caption_tiktok.txt").write_text(caption_menarik(naskah, kategori) + "\n", encoding="utf-8")
