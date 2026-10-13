import random
import re
import time

from pydantic import BaseModel, ConfigDict, Field

from . import config


class Naskah(BaseModel):
    model_config = ConfigDict(extra="ignore")

    topik: str = Field(description="Masalah kerja spesifik yang dibahas, maksimal 8 kata")
    judul: str = Field(description="Judul YouTube Shorts, maksimal 60 karakter, tanpa hashtag dan emoji")
    deskripsi: str = Field(description="Deskripsi video 2-3 kalimat")
    tags: list[str] = Field(description="5-8 tag pencarian, huruf kecil")
    hook: str = Field(description="Kalimat pembuka, maksimal 14 kata, langsung menyebut masalahnya")
    narasi_prompt: str = Field(description="1-2 kalimat narasi saat prompt ditampilkan, jangan membacakan prompt kata per kata")
    prompt: str = Field(description="Prompt lengkap yang bisa langsung dicontek, 150-380 karakter, pakai [placeholder] untuk data penonton")
    narasi_hasil: str = Field(description="1-3 kalimat narasi saat hasil AI ditampilkan")
    hasil: str = Field(description="Contoh jawaban AI yang realistis, maksimal 450 karakter, boleh baris baru dan '- ' untuk poin, tanpa markdown")
    narasi_trik: str = Field(description="1-2 kalimat narasi tentang trik tambahan")
    trik: str = Field(description="Satu kalimat tambahan untuk ditempel di akhir prompt, maksimal 120 karakter")
    topik_besok: str = Field(description="Topik video berikutnya dalam kategori berikutnya, maksimal 8 kata")
    penutup: str = Field(description="1-2 kalimat penutup: ajak simpan video dan sebut topik video berikutnya")
    gambar_hook: str = Field(description="English image prompt for the hook scene: a person in the problem situation, emotional, cinematic")
    gambar_kerja: str = Field(description="English image prompt for the working scene: close-up of hands, laptop or phone, workspace, no readable screen text")
    gambar_trik: str = Field(description="English image prompt for the tip scene: a relieved or confident person, bright mood")
    gambar_penutup: str = Field(description="English image prompt for the closing scene, related to the next video topic")


GAYA_HOOK = [
    "pertanyaan tentang situasi kerja yang sangat relatable",
    "sebut waktu yang bisa dihemat, misalnya 'dari 1 jam jadi 2 menit'",
    "sebut kesalahan yang sering dilakukan orang",
    "mulai dengan 'Berhenti ...' lalu tawarkan cara yang lebih cepat",
    "gambarkan momen panik yang spesifik, misalnya deadline jam 4 sore",
]

NARASI_FIELDS = ["hook", "narasi_prompt", "narasi_hasil", "narasi_trik", "penutup"]

_NON_BMP = re.compile(r"[\U00010000-\U0010FFFF\u2600-\u27BF\uFE0F]")


def _bersihkan(teks: str) -> str:
    teks = _NON_BMP.sub("", teks)
    teks = teks.replace("**", "").replace("__", "")
    teks = re.sub(r"^\s*#+\s*", "", teks, flags=re.M)
    teks = re.sub(r"^\s*[*•]\s+", "- ", teks, flags=re.M)
    return teks.strip()


def rapikan(n: Naskah) -> Naskah:
    data = {k: (_bersihkan(v) if isinstance(v, str) else v) for k, v in n.model_dump().items()}
    data["tags"] = [_bersihkan(t).lower() for t in n.tags if t.strip()][:8]
    data["hasil"] = re.sub(r"\s+-\s+(?=[A-Z0-9])", "\n- ", data["hasil"])
    data["hasil"] = re.sub(r"\s+(?=\d+\.\s+[A-Z])", "\n", data["hasil"])
    return Naskah(**data)


def jumlah_kata_narasi(n: Naskah) -> int:
    return sum(len(getattr(n, f).split()) for f in NARASI_FIELDS)


def _masalah(n: Naskah, label_berikut: str) -> list[str]:
    masalah = []
    kata = jumlah_kata_narasi(n)
    if not 80 <= kata <= 135:
        masalah.append(f"total narasi {kata} kata, harus 80-135 kata")
    if len(n.prompt) > 450:
        masalah.append(f"prompt {len(n.prompt)} karakter, maksimal 380")
    if len(n.hasil) > 560:
        masalah.append(f"hasil {len(n.hasil)} karakter, maksimal 450")
    if len(n.trik) > 160:
        masalah.append(f"trik {len(n.trik)} karakter, maksimal 120")
    if label_berikut.split()[-1] not in n.penutup.lower():
        masalah.append(f"penutup harus menyebut '{label_berikut}' dan topik video berikutnya")
    gambar = [n.gambar_hook, n.gambar_kerja, n.gambar_trik, n.gambar_penutup]
    if any(len(g.split()) < 5 for g in gambar):
        masalah.append("setiap prompt gambar minimal 5 kata bahasa Inggris")
    return masalah


def _instruksi(kategori, kategori_besok, label_berikut, topik, hindari, rekap_minggu) -> str:
    nama_kat, cakupan = kategori
    nama_besok, cakupan_besok = kategori_besok
    topik_baris = (
        f"Topik video ini SUDAH DITENTUKAN (sudah dijanjikan di video sebelumnya): {topik}"
        if topik
        else "Pilih sendiri satu masalah kerja yang sempit, spesifik, dan sering dialami orang Indonesia. Jangan tips umum."
    )
    hindari_baris = "\n".join(f"- {t}" for t in hindari) or "- (belum ada)"
    rekap_baris = ""
    if rekap_minggu:
        rekap_baris = "Video minggu ini (boleh dirujuk untuk rekap):\n" + "\n".join(f"- {t}" for t in rekap_minggu) + "\n"

    return f"""Kamu penulis naskah untuk channel YouTube Shorts dan TikTok bernama "{config.CHANNEL_NAME}".
Channel ini mengajarkan cara memakai AI (ChatGPT, Gemini, atau sejenisnya) untuk pekerjaan sehari-hari orang Indonesia.
Setiap video membahas SATU masalah kerja dan memberi SATU prompt yang bisa langsung dicontek.

Kategori video ini: {nama_kat} ({cakupan}).
{topik_baris}
Gaya hook: {random.choice(GAYA_HOOK)}.

Jangan ulangi topik yang sudah pernah dibuat:
{hindari_baris}
{rekap_baris}
Video berikutnya tayang {label_berikut}, kategori {nama_besok} ({cakupan_besok}).
Isi topik_besok dengan topik spesifik dari kategori itu, dan di penutup sebut "{label_berikut}" beserta topiknya.

Setiap adegan memakai gambar latar buatan AI. Tulis prompt gambarnya dalam bahasa Inggris (gambar_hook, gambar_kerja,
gambar_trik, gambar_penutup): deskripsi visual yang konkret, orang Indonesia di kantor/rumah/toko sesuai topik,
tanpa tulisan atau layar yang bisa dibaca. Jangan sebut merek atau tokoh nyata.

Struktur video (35-50 detik):
1. hook: masalahnya, langsung, tanpa basa-basi atau sapaan.
2. narasi_prompt: arahkan penonton ke prompt di layar.
3. narasi_hasil: jelaskan apa yang didapat dari AI.
4. narasi_trik: satu trik kecil yang membuat hasilnya lebih bagus.
5. penutup: ajak simpan video dan sebut topik video berikutnya.

Aturan:
- Bahasa Indonesia santai tapi jelas, sapa penonton dengan "kamu".
- Total narasi (hook + narasi_prompt + narasi_hasil + narasi_trik + penutup) 90-125 kata.
- Narasi akan dibacakan suara AI, jadi tulis angka dan singkatan yang mudah diucapkan.
- Prompt harus benar-benar berguna dan spesifik: peran, tugas, format keluaran, batasan.
- Hasil adalah contoh jawaban AI yang realistis dan singkat, bukan janji.
- Tanpa emoji, tanpa markdown, tanpa hashtag, tanpa klaim statistik yang dikarang.
- Jangan sebut nama channel di hook.
"""


def buat_naskah(kategori, kategori_besok, label_berikut, topik=None, hindari=(), rekap_minggu=()) -> tuple[Naskah, str | None]:
    if not config.GEMINI_API_KEY:
        raise SystemExit("GEMINI_API_KEY belum diisi di file .env (ambil gratis di https://aistudio.google.com/apikey).")

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=config.GEMINI_API_KEY)
    instruksi = _instruksi(kategori, kategori_besok, label_berikut, topik, list(hindari)[-40:], list(rekap_minggu))
    catatan = ""
    error_terakhir = None
    terakhir = None

    daftar_model = list(dict.fromkeys([config.GEMINI_MODEL, *config.GEMINI_MODEL_CADANGAN]))

    for model in daftar_model:
        for percobaan in range(1, 3):
            try:
                resp = client.models.generate_content(
                    model=model,
                    contents=instruksi + catatan,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=Naskah,
                        temperature=0.9,
                    ),
                )
                naskah = resp.parsed if isinstance(resp.parsed, Naskah) else Naskah.model_validate_json(resp.text)
                naskah = rapikan(naskah)
                if topik:
                    naskah.topik = topik
                terakhir = naskah
                masalah = _masalah(naskah, label_berikut)
                if not masalah:
                    print(f"  Model: {model}")
                    return naskah, None
                print(f"  Naskah dari {model} belum pas: {'; '.join(masalah)}")
                catatan = "\n\nPerbaiki dari percobaan sebelumnya: " + "; ".join(masalah) + "."
                error_terakhir = "; ".join(masalah)
            except Exception as e:
                error_terakhir = e
                kode = getattr(e, "code", None)
                print(f"  {model} gagal ({kode or type(e).__name__}): {str(e)[:120]}")
                if kode in (429, 500, 503, 404):
                    time.sleep(3)
                    break
                time.sleep(5)

    if terakhir is not None:
        catatan = f"Naskah dipakai walau belum ideal: {error_terakhir}"
        print(f"  {catatan}")
        return terakhir, catatan
    raise RuntimeError(f"Semua model Gemini gagal. Error terakhir: {error_terakhir}")
