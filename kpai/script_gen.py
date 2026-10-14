import json
import random
import re
import time
from dataclasses import dataclass, field

import requests
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from . import config
from .errors import Jenis, dari_response, klasifikasi_exception


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


@dataclass
class HasilNaskah:
    naskah: Naskah
    provider: str
    model: str
    fallback_dari: str | None = None
    alasan: str | None = None
    peringatan: str | None = None
    konfigurasi: list[str] = field(default_factory=list)


def _baca_json(teks: str) -> Naskah:
    mentah = teks.strip()
    if mentah.startswith("```"):
        mentah = re.sub(r"^```(?:json)?", "", mentah).strip()
        mentah = re.sub(r"```$", "", mentah).strip()
    return rapikan(Naskah.model_validate_json(mentah))


def _gemini(klien, instruksi, catatan, topik, label_berikut, tidur) -> tuple[Naskah | None, str, list[str], str | None]:
    from google.genai import types

    daftar_model = list(dict.fromkeys([config.GEMINI_MODEL, *config.GEMINI_MODEL_CADANGAN]))
    terakhir, masalah_terakhir = None, ""
    sudah_menunggu = False
    notifikasi = []
    alasan = "gagal"

    for model in daftar_model:
        for _percobaan in range(2):
            try:
                resp = klien.models.generate_content(
                    model=model,
                    contents=instruksi + catatan,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=Naskah,
                        temperature=0.9,
                    ),
                )
                naskah = resp.parsed if isinstance(resp.parsed, Naskah) else _baca_json(resp.text)
                if topik:
                    naskah.topik = topik
                masalah = _masalah(naskah, label_berikut)
                if not masalah:
                    print(f"  Model: {model}")
                    return naskah, "", notifikasi, None
                print(f"  Naskah dari {model} belum pas: {'; '.join(masalah)}")
                catatan = "\n\nPerbaiki dari percobaan sebelumnya: " + "; ".join(masalah) + "."
                terakhir, masalah_terakhir = naskah, "; ".join(masalah)
            except Exception as e:
                salah = klasifikasi_exception("Gemini", e)
                print(f"  Gemini {model} gagal ({salah.jenis.value}): {salah.pesan}")
                if salah.jenis == Jenis.INVALID_KEY:
                    notifikasi.append("Konfigurasi Gemini tidak valid. Periksa GEMINI_API_KEY. Provider ini tidak dicoba lagi.")
                    return None, "API key invalid", notifikasi, None
                if salah.jenis == Jenis.QUOTA:
                    print("  Kuota Gemini habis, pindah tanpa mengulang model Gemini yang lain.")
                    return None, "quota limit", notifikasi, None
                if salah.jenis == Jenis.RATE_LIMIT and not sudah_menunggu:
                    jeda = min(salah.retry_after or 3, 60)
                    print(f"  Gemini rate limit sementara, menunggu {jeda:.0f} detik.")
                    tidur(jeda)
                    sudah_menunggu = True
                    continue
                if salah.jenis == Jenis.RATE_LIMIT:
                    return None, "rate limit", notifikasi, None
                alasan = salah.jenis.value.replace("_", " ")
                if salah.jenis == Jenis.MODEL_UNAVAILABLE:
                    break
                if salah.jenis in (Jenis.SERVER, Jenis.TIMEOUT):
                    tidur(2)
                    break
                break
    if terakhir is not None:
        return terakhir, "", notifikasi, f"Naskah Gemini dipakai walau belum ideal: {masalah_terakhir}"
    return None, alasan, notifikasi, None


def _groq(instruksi, topik, label_berikut, pengirim, tidur) -> tuple[Naskah | None, str, list[str]]:
    if not config.GROQ_API_KEY:
        print("  Groq dinonaktifkan: GROQ_API_KEY belum dikonfigurasi.")
        return None, "GROQ_API_KEY belum dikonfigurasi", []
    if not config.GROQ_MODEL:
        print("  Groq dinonaktifkan: GROQ_MODEL belum dikonfigurasi.")
        return None, "GROQ_MODEL belum dikonfigurasi", []

    sudah_menunggu = False
    notifikasi = []
    prompt = instruksi + "\n\nBalas hanya JSON dengan kunci: " + ", ".join(Naskah.model_fields) + "."
    for percobaan in range(2):
        try:
            respon = pengirim(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {config.GROQ_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": config.GROQ_MODEL,
                    "temperature": 0.7,
                    "messages": [
                        {"role": "system", "content": "Balas hanya dengan satu objek JSON, tanpa markdown."},
                        {"role": "user", "content": prompt},
                    ],
                    "response_format": {"type": "json_object"},
                },
                timeout=90,
            )
            salah = dari_response("Groq", respon)
            if salah:
                raise salah
            isi = respon.json()["choices"][0]["message"]["content"]
            naskah = _baca_json(isi)
            if topik:
                naskah.topik = topik
            masalah = _masalah(naskah, label_berikut)
            if masalah and percobaan == 0:
                prompt = instruksi + "\n\nPerbaiki: " + "; ".join(masalah) + ". Balas hanya JSON."
                continue
            if masalah:
                return naskah, "", []
            print(f"  Model: {config.GROQ_MODEL}")
            return naskah, "", notifikasi
        except (ValidationError, KeyError, json.JSONDecodeError, TypeError) as e:
            print(f"  Groq gagal (permanent): {str(e)[:160]}")
            return None, "respons tidak valid", notifikasi
        except Exception as e:
            salah = klasifikasi_exception("Groq", e)
            print(f"  Groq gagal ({salah.jenis.value}): {salah.pesan}")
            if salah.jenis == Jenis.INVALID_KEY:
                notifikasi.append("Konfigurasi Groq tidak valid. Periksa GROQ_API_KEY. Provider ini tidak dicoba lagi.")
                return None, "API key invalid", notifikasi
            if salah.jenis == Jenis.QUOTA:
                return None, "quota limit", notifikasi
            if salah.jenis == Jenis.RATE_LIMIT and not sudah_menunggu:
                jeda = min(salah.retry_after or 3, 60)
                print(f"  Groq rate limit sementara, menunggu {jeda:.0f} detik.")
                tidur(jeda)
                sudah_menunggu = True
                continue
            if salah.jenis in (Jenis.SERVER, Jenis.TIMEOUT) and percobaan == 0:
                tidur(2)
                continue
            return None, salah.jenis.value.replace("_", " "), notifikasi
    return None, "gagal", notifikasi


def buat_naskah(kategori, kategori_besok, label_berikut, topik=None, hindari=(), rekap_minggu=(), klien=None, pengirim=None, tidur=None) -> HasilNaskah:
    from .template_naskah import template_lokal

    pengirim = pengirim or requests.post
    tidur = tidur or time.sleep
    instruksi = _instruksi(kategori, kategori_besok, label_berikut, topik, list(hindari)[-40:], list(rekap_minggu))
    konfigurasi = []
    alasan_gemini = ""
    naskah = None
    peringatan = None

    if klien is not None or config.GEMINI_API_KEY:
        if klien is None:
            from google import genai
            klien = genai.Client(api_key=config.GEMINI_API_KEY)
        naskah, alasan_gemini, notifikasi, peringatan = _gemini(klien, instruksi, "", topik, label_berikut, tidur)
        konfigurasi.extend(notifikasi)
        if naskah is not None and peringatan is None:
            return HasilNaskah(naskah, "Gemini", config.GEMINI_MODEL, konfigurasi=konfigurasi)
        if naskah is not None and not config.TEXT_FALLBACK_ENABLED:
            return HasilNaskah(naskah, "Gemini", config.GEMINI_MODEL, peringatan=peringatan, konfigurasi=konfigurasi)
    else:
        alasan_gemini = "GEMINI_API_KEY belum dikonfigurasi"
        print(f"  Gemini dinonaktifkan: {alasan_gemini}.")

    if not config.TEXT_FALLBACK_ENABLED:
        if naskah is not None:
            return HasilNaskah(naskah, "Gemini", config.GEMINI_MODEL, peringatan=peringatan, konfigurasi=konfigurasi)
        raise RuntimeError(f"Gemini gagal ({alasan_gemini}) dan TEXT_FALLBACK_ENABLED=false.")

    if naskah is not None and peringatan:
        print(f"  {peringatan}. Mencoba Groq sebelum memakai naskah yang belum ideal.")

    groq_naskah, alasan_groq, notifikasi_groq = _groq(instruksi, topik, label_berikut, pengirim, tidur)
    konfigurasi.extend(notifikasi_groq)
    if groq_naskah is not None and not _masalah(groq_naskah, label_berikut):
        return HasilNaskah(
            groq_naskah, "Groq", config.GROQ_MODEL,
            fallback_dari="Gemini", alasan=alasan_gemini or "naskah belum ideal", konfigurasi=konfigurasi,
        )

    if naskah is not None:
        catatan = peringatan or f"Naskah Gemini dipakai walau belum ideal: {alasan_groq}"
        return HasilNaskah(naskah, "Gemini", config.GEMINI_MODEL, peringatan=catatan, konfigurasi=konfigurasi)

    print(f"  Memakai template lokal. Gemini: {alasan_gemini}. Groq: {alasan_groq}.")
    alasan = alasan_gemini or "gagal"
    if alasan_groq and alasan_groq not in alasan:
        alasan = f"{alasan}, lalu Groq karena {alasan_groq}"
    return HasilNaskah(
        template_lokal(kategori, kategori_besok, label_berikut, topik),
        "Template lokal", "template",
        fallback_dari="Gemini", alasan=alasan, konfigurasi=konfigurasi,
    )
