"""Deteksi topik yang beda judul tetapi intinya sama."""

import re

_FRASE = (
    ("kecerdasan buatan", "ai"),
    ("artificial intelligence", "ai"),
    ("matahari", "matahari"),
    ("tiba-tiba", " "),
)

_PETA = {
    "menghilang": "hilang",
    "lenyap": "hilang",
    "raib": "hilang",
    "menghilangnya": "hilang",
    "mentari": "matahari",
    "bernafas": "napas",
    "bernapas": "napas",
    "berputar": "putar",
    "rotasi": "putar",
    "gravitasi": "gravitasi",
    "gravity": "gravitasi",
}

_STOP = {
    "yang", "dan", "dari", "untuk", "dengan", "pada", "adalah", "ini", "itu", "akan",
    "jika", "bagaimana", "kalau", "atau", "sebuah", "para", "dalam", "skenario", "fiksi",
    "menjadi", "lebih", "selama", "detik", "semua", "dunia", "tiba", "sekitar", "setelah",
    "sebelum", "karena", "supaya", "agar", "sudah", "masih", "tidak", "bukan", "ada",
    "ke", "di", "ke", "ya", "kah", "pun", "lah", "nya", "the", "and", "what",
}


def normalkan(teks: str) -> set[str]:
    mentah = (teks or "").lower()
    for sumber, ganti in _FRASE:
        mentah = mentah.replace(sumber, ganti)
    token = []
    for kata in re.findall(r"[a-z0-9]+", mentah):
        kata = _PETA.get(kata, kata)
        if kata in _STOP or len(kata) < 3:
            continue
        token.append(kata)
    return set(token)


def mirip(kiri: str, kanan: str) -> bool:
    if not kiri or not kanan:
        return False
    a, b = normalkan(kiri), normalkan(kanan)
    if not a or not b:
        return False
    if a == b:
        return True
    kecil, besar = (a, b) if len(a) <= len(b) else (b, a)
    if len(kecil) >= 2 and kecil <= besar:
        return True
    irisan = a & b
    if not irisan:
        return False
    return len(irisan) / len(a | b) >= 0.65


def mirip_dengan_daftar(topik: str, inti: str, daftar) -> str:
    for lama in daftar:
        if mirip(topik, lama) or (inti and mirip(inti, lama)):
            return str(lama)
    return ""
