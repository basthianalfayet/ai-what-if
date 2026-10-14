def _baris_teks(hasil) -> str:
    if hasil.fallback_dari and hasil.alasan:
        return f"{hasil.provider} (fallback dari {hasil.fallback_dari} karena {hasil.alasan})"
    return hasil.provider


def _baris_gambar(catatan: list) -> str:
    if not catatan:
        return "tidak ada"
    penyedia = []
    for item in catatan:
        if item.provider not in penyedia:
            penyedia.append(item.provider)
    if len(penyedia) == 1:
        return penyedia[0]
    return "; ".join(f"{item.scene} {item.provider}" for item in catatan)


def _baris_biaya(catatan: list) -> str:
    angka = [item.biaya_usd for item in catatan if item.biaya_usd]
    if not angka:
        return "$0"
    return f"${sum(angka):.4f}"


def laporan_selesai(hasil_naskah, catatan_gambar: list) -> str:
    return (
        "Job selesai.\n"
        f"Text: {_baris_teks(hasil_naskah)}.\n"
        f"Image: {_baris_gambar(catatan_gambar)}.\n"
        "Visual check: PASS.\n"
        f"Biaya fallback: {_baris_biaya(catatan_gambar)}."
    )


def laporan_needs_review(hasil_naskah, alasan: str, peringatan: list[str]) -> str:
    teks = _baris_teks(hasil_naskah) if hasil_naskah is not None else "belum ada"
    ekstra = ""
    if peringatan:
        ekstra = "\n" + "\n".join(f"- {p}" for p in peringatan)
    return (
        "Job berhenti: NEEDS_REVIEW.\n"
        f"Text: {teks}.\n"
        f"Image: {alasan}\n"
        "Visual check: FAIL.\n"
        "Render tidak dilanjutkan."
        f"{ekstra}"
    )
