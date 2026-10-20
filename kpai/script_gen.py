import json
import re
import time
from dataclasses import dataclass, field

import requests
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from . import config
from .errors import Jenis, dari_response, klasifikasi_exception
from .mode import cooldown_kuota, dalam_cooldown, fallback_naskah_lokal, boleh_naskah_api, catat_cooldown, mode
from .topik import mirip_dengan_daftar


class AdeganNaskah(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="hook, awal, puncak, atau penutup")
    narasi: str = Field(description="Teks yang dibacakan, bahasa Indonesia")
    visual: str = Field(description="Deskripsi visual bahasa Indonesia untuk editor")
    prompt_gambar: str = Field(description="Prompt gambar bahasa Inggris, konkret, tanpa teks")
    subtitle: str = Field(description="Sama dengan narasi, karena subtitle mengikuti audio")
    judul_layar: str = Field(description="Teks pendek di layar, maksimal 8 kata")
    sfx: str = Field(default="whoosh", description="whoosh, pop, atau none")


class Naskah(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id_video: str = ""
    topik: str
    kategori: str = ""
    inti: str = ""
    judul_kerja: str
    hook: str
    adegan: list[AdeganNaskah]
    penjelasan_ilmiah: str
    batas_ketidakpastian: str
    ending: str
    pertanyaan_komentar: str
    judul_youtube: str
    deskripsi_youtube: str
    hashtag: list[str] = Field(default_factory=list)
    referensi: list[str] = Field(default_factory=list)
    pengungkapan_sintetis: bool = True
    perlu_tinjauan: bool = False
    topik_berikut: str = ""
    topik_ketiga: str = ""
    judul_seri: str = ""
    urutan_seri: int = 1


AJAKAN_SUBSCRIBE = "Subscribe kalau mau skenario berikutnya."

_NON_BMP = re.compile(r"[\U00010000-\U0010FFFF\u2600-\u27BF\uFE0F]")
_URUTAN = config.URUTAN_ADEGAN


def _bersihkan(teks: str) -> str:
    teks = _NON_BMP.sub("", teks or "")
    teks = teks.replace("**", "").replace("__", "")
    teks = re.sub(r"^\s*#+\s*", "", teks, flags=re.M)
    return teks.strip()


def pertanyaan(teks: str, batas: int = 90) -> str:
    """Judul yang langsung bertanya, bukan judul puitis."""
    t = " ".join((teks or "").split()).strip(" \"'")
    if not t:
        return ""
    rendah = t.casefold()
    if rendah.startswith("bagaimana jika "):
        isi = t[15:].strip()
    elif rendah.startswith("jika "):
        isi = t[5:].strip()
    else:
        isi = t
    isi = isi.strip(" ?.!")
    if not isi:
        return ""
    hasil = "Bagaimana jika " + isi[0].upper() + isi[1:]
    if not hasil.endswith("?"):
        hasil += "?"
    if len(hasil) > batas:
        hasil = hasil[: batas - 1].rstrip(" ?.!,;:") + "?"
    return hasil


def adalah_pertanyaan(teks: str) -> bool:
    t = " ".join((teks or "").split())
    return t.casefold().startswith("bagaimana jika ") and t.endswith("?")


def _tanpa_ajakan(teks: str) -> str:
    return re.sub(
        r"\s*Subscribe kalau mau skenario berikutnya\.?\s*$",
        "",
        teks or "",
        flags=re.IGNORECASE,
    ).strip()


def _akhiri_ajakan(narasi: str) -> str:
    dasar = _tanpa_ajakan(narasi).rstrip()
    if not dasar:
        return AJAKAN_SUBSCRIBE
    if dasar[-1] not in ".?!":
        dasar += "."
    return f"{dasar} {AJAKAN_SUBSCRIBE}"


def rapikan(n: Naskah) -> Naskah:
    data = n.model_dump()
    for kunci, nilai in list(data.items()):
        if isinstance(nilai, str):
            data[kunci] = _bersihkan(nilai)
    adegan = []
    for urut, item in zip(_URUTAN, data.get("adegan") or []):
        if len(adegan) >= len(_URUTAN):
            break
        item = dict(item)
        item["id"] = urut
        for kunci in ("narasi", "visual", "prompt_gambar", "subtitle", "judul_layar", "sfx"):
            item[kunci] = _bersihkan(str(item.get(kunci) or ""))
        if not item["subtitle"]:
            item["subtitle"] = item["narasi"]
        if not item["judul_layar"]:
            item["judul_layar"] = " ".join(item["narasi"].split()[:6])
        if item["sfx"] not in ("whoosh", "pop", "none"):
            item["sfx"] = "pop"
        if urut == "penutup":
            item["narasi"] = _akhiri_ajakan(item["narasi"])
            item["subtitle"] = item["narasi"]
        adegan.append(item)
    data["adegan"] = adegan
    data["hashtag"] = [_bersihkan(t).lstrip("#").lower() for t in data.get("hashtag") or [] if str(t).strip()][:8]
    data["referensi"] = [_bersihkan(t) for t in data.get("referensi") or [] if str(t).strip()][:6]
    if not data.get("inti"):
        data["inti"] = data.get("topik") or ""
    if not data.get("pengungkapan_sintetis"):
        data["pengungkapan_sintetis"] = True
    judul = pertanyaan(data.get("judul_youtube") or data.get("judul_kerja") or data.get("topik") or "")
    if judul:
        data["judul_youtube"] = judul
        data["judul_kerja"] = judul
    for kunci in ("topik_berikut", "topik_ketiga"):
        if str(data.get(kunci) or "").strip():
            data[kunci] = pertanyaan(data[kunci])
    try:
        urutan = int(data.get("urutan_seri") or 1)
    except (TypeError, ValueError):
        urutan = 1
    data["urutan_seri"] = urutan if urutan in (1, 2, 3) else 1
    data["judul_seri"] = _bersihkan(str(data.get("judul_seri") or ""))
    return Naskah(**data)


def jumlah_kata_narasi(n: Naskah) -> int:
    return sum(len(_tanpa_ajakan(a.narasi).split()) for a in n.adegan)


def _masalah(n: Naskah, label_berikut: str = "", lanjutan: bool = False) -> list[str]:
    del label_berikut
    masalah = []
    kata = jumlah_kata_narasi(n)
    if not 90 <= kata <= 155:
        masalah.append(f"total narasi {kata} kata, harus 90-155 kata")
    if [a.id for a in n.adegan] != list(_URUTAN):
        masalah.append("adegan harus hook, awal, puncak, lalu penutup")
    if not 8 <= len(n.hook.split()) <= 28:
        masalah.append("hook 8-28 kata")
    if not adalah_pertanyaan(n.judul_youtube):
        masalah.append("judul YouTube harus pertanyaan Bagaimana jika")
    if len(n.judul_youtube) > 100:
        masalah.append("judul YouTube maksimal 100 karakter")
    if not lanjutan and n.urutan_seri <= 1:
        if not (n.judul_seri or "").strip():
            masalah.append("judul seri kosong")
        if not adalah_pertanyaan(n.topik_berikut) or not adalah_pertanyaan(n.topik_ketiga):
            masalah.append("bagian 2 dan 3 harus pertanyaan Bagaimana jika")
        if n.topik_berikut.casefold() == n.topik_ketiga.casefold():
            masalah.append("bagian 2 dan 3 tidak boleh sama")
    if len(n.penjelasan_ilmiah.split()) < 12 or len(n.batas_ketidakpastian.split()) < 12:
        masalah.append("penjelasan ilmiah dan batas ketidakpastian masing-masing minimal 12 kata")
    if len(n.ending.split()) < 8 or len(n.pertanyaan_komentar.split()) < 6:
        masalah.append("ending dan pertanyaan komentar terlalu pendek")
    for adegan in n.adegan:
        if len(adegan.narasi.split()) < 12:
            masalah.append(f"narasi {adegan.id} minimal 12 kata")
        if len(adegan.prompt_gambar.split()) < 5:
            masalah.append(f"prompt gambar {adegan.id} minimal 5 kata bahasa Inggris")
        if len(adegan.judul_layar.split()) > 10:
            masalah.append(f"judul layar {adegan.id} maksimal 10 kata")
    return masalah


def _baris_seri(seri) -> str:
    if not seri:
        return (
            "Mulai seri baru yang terdiri dari 3 video satu benang, bukan tiga topik acak.\n"
            "judul_seri maksimal 6 kata.\n"
            "Video ini bagian 1. Di adegan penutup, sebut sekali bahwa ini bagian 1 dari 3.\n"
            "topik_berikut adalah bagian 2, topik_ketiga adalah bagian 3. "
            "Keduanya pertanyaan yang diawali Bagaimana jika dan masih akibat dari cerita ini.\n"
            "urutan_seri harus 1."
        )
    nomor = int(seri["selesai"]) + 1
    if nomor >= 3:
        return (
            f'Ini bagian 3 dari 3 dalam seri "{seri["nama"]}". '
            "Jangan mengarang bagian keempat. Di adegan penutup, sebut sekali bahwa seri ini selesai."
        )
    berikut = seri["bagian"][nomor] if nomor < len(seri["bagian"]) else ""
    return (
        f'Ini bagian {nomor} dari 3 dalam seri "{seri["nama"]}".\n'
        f"Bagian berikutnya sudah ditentukan: {berikut}. Jangan mengganti benangnya.\n"
        f"Di adegan penutup, sebut sekali bahwa ini bagian {nomor} dari 3."
    )


def _instruksi(kategori, kategori_besok, label_berikut, topik, hindari, rekap_minggu, seri=None) -> str:
    del label_berikut, rekap_minggu
    nama_kat, cakupan = kategori
    nama_besok, _cakupan_besok = kategori_besok
    topik_baris = (
        f"Topik video ini SUDAH DITENTUKAN: {topik}. Jangan mengganti inti ceritanya."
        if topik
        else "Pilih sendiri satu skenario what-if yang sempit, visual, dan belum jenuh. Jangan tips umum."
    )
    hindari_baris = "\n".join(f"- {t}" for t in hindari) or "- (belum ada)"
    return f"""Kamu penulis naskah YouTube Shorts untuk channel "{config.CHANNEL_NAME}".
Bahasa Indonesia yang alami. Setiap video menjawab satu pertanyaan "bagaimana jika" tentang sains, alam, tubuh, hewan, teknologi, atau masa depan.
Ini skenario fiksi. Bedakan mekanisme yang didukung pengetahuan umum dari bagian yang hanya spekulasi. Jangan menyajikan fiksi sebagai kejadian nyata.
Jangan menyalin naskah kreator lain. Jangan mengarang statistik, tahun, atau kutipan.

Kategori: {nama_kat} ({cakupan}).
{topik_baris}
{_baris_seri(seri)}
Gaya hook: pertanyaan langsung yang selesai dalam satu napas.
Jangan mengulang inti cerita berikut:
{hindari_baris}
Kategori slot berikutnya hanya sebagai pengingat keragaman, bukan untuk disebut di narasi: {nama_besok}.

Struktur tepat 4 adegan, id berurutan hook, awal, puncak, penutup:
1. hook: pertanyaan yang berhentiin scroll dalam 1-2 detik, lalu satu fakta waktu atau skala.
2. awal: akibat pertama yang masuk akal.
3. puncak: akibat yang berkembang. Sebut bagian yang tidak pasti.
4. penutup: payoff yang memuaskan, ingatkan bahwa ini skenario, lalu pertanyaan komentar. Jangan menulis kata subscribe.

Aturan:
- Total narasi 100-140 kata. Tiap narasi minimal 12 kata. Jangan menghitung kalimat subscribe; sistem yang menambahkan.
- subtitle tiap adegan sama dengan narasinya.
- judul_layar maksimal 8 kata, tanpa emoji.
- prompt_gambar bahasa Inggris, visual sinematik, tanpa tulisan, tanpa merek, tanpa tokoh nyata.
- penjelasan_ilmiah hanya memuat hal yang kamu yakini sebagai pengetahuan umum.
- batas_ketidakpastian menyebut apa yang tidak boleh dianggap pasti.
- judul_kerja dan judul_youtube wajib sama, diawali "Bagaimana jika", diakhiri tanda tanya, maksimal 90 karakter, tanpa emoji, tanpa judul puitis.
- hashtag 5 sampai 8, huruf kecil, tanpa tanda pagar.
- pengungkapan_sintetis harus true.
- inti berisi 2-4 kata kunci unik cerita, misalnya "matahari hilang".
- Jangan sebut nama channel di hook.
"""


def terapkan_seri(naskah: Naskah, seri: dict) -> Naskah:
    """Kunci episode yang sudah direncanakan supaya model tidak membelokkan benangnya."""
    nomor = int(seri["selesai"]) + 1
    naskah.urutan_seri = nomor if nomor in (1, 2, 3) else 1
    naskah.judul_seri = str(seri.get("nama") or naskah.judul_seri)
    naskah.topik = seri["bagian"][nomor - 1]
    naskah.judul_youtube = pertanyaan(naskah.topik)
    naskah.judul_kerja = naskah.judul_youtube
    naskah.topik_berikut = seri["bagian"][nomor] if nomor < 3 else ""
    naskah.topik_ketiga = ""
    if seri.get("kategori"):
        naskah.kategori = seri["kategori"]
    return naskah


@dataclass
class HasilNaskah:
    naskah: Naskah
    provider: str
    model: str
    fallback_dari: str | None = None
    alasan: str | None = None
    peringatan: str | None = None
    konfigurasi: list[str] = field(default_factory=list)
    percobaan: int = 0
    ditolak: bool = False


def _baca_json(teks: str) -> Naskah:
    mentah = (teks or "").strip()
    if not mentah:
        raise ValueError("respons kosong")
    if mentah.startswith("```"):
        mentah = re.sub(r"^```(?:json)?", "", mentah).strip()
        mentah = re.sub(r"```$", "", mentah).strip()
    return rapikan(Naskah.model_validate_json(mentah))


def _mirip(naskah: Naskah, hindari) -> str:
    return mirip_dengan_daftar(naskah.topik, naskah.inti, list(hindari or []))


def _gemini(klien, instruksi, topik, label_berikut, hindari, tidur, lanjutan=False) -> tuple[Naskah | None, str, list[str], str | None, int]:
    from google.genai import types

    if dalam_cooldown("gemini"):
        print("  Gemini sedang cooldown, tidak dipanggil.")
        return None, "cooldown", [], None, 0
    daftar_model = list(dict.fromkeys([config.GEMINI_MODEL, *config.GEMINI_MODEL_CADANGAN]))
    terakhir, masalah_terakhir = None, ""
    sudah_menunggu = False
    notifikasi = []
    alasan = "gagal"
    percobaan = 0
    catatan = ""

    for model in daftar_model:
        for _giliran in range(config.MAX_RETRY):
            percobaan += 1
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
                if isinstance(resp.parsed, Naskah):
                    naskah = rapikan(resp.parsed)
                else:
                    naskah = _baca_json(getattr(resp, "text", "") or "")
                if topik:
                    naskah.topik = topik
                masalah = _masalah(naskah, label_berikut, lanjutan)
                bentrok = "" if topik else _mirip(naskah, hindari)
                if bentrok:
                    masalah.append(f"terlalu mirip dengan {bentrok}")
                if not masalah:
                    print(f"  Model: {model}")
                    return naskah, "", notifikasi, None, percobaan
                print(f"  Naskah dari {model} belum pas: {'; '.join(masalah)}")
                catatan = "\n\nPerbaiki dari percobaan sebelumnya: " + "; ".join(masalah) + "."
                terakhir, masalah_terakhir = naskah, "; ".join(masalah)
            except Exception as e:
                salah = klasifikasi_exception("Gemini", e)
                print(f"  Gemini {model} gagal ({salah.jenis.value}): {salah.pesan}")
                if salah.jenis == Jenis.INVALID_KEY:
                    notifikasi.append("Konfigurasi Gemini tidak valid. Periksa GEMINI_API_KEY. Provider ini tidak dicoba lagi.")
                    catat_cooldown("gemini", 24)
                    return None, "API key invalid", notifikasi, None, percobaan
                if salah.jenis in (Jenis.QUOTA, Jenis.BILLING):
                    print("  Kuota atau billing Gemini habis, pindah tanpa mengulang model lain.")
                    cooldown_kuota("gemini")
                    alasan = "quota limit" if salah.jenis == Jenis.QUOTA else "billing"
                    return None, alasan, notifikasi, None, percobaan
                if salah.jenis == Jenis.RATE_LIMIT and not sudah_menunggu:
                    from .errors import jeda_sementara
                    jeda = min(salah.retry_after or jeda_sementara(0), 60)
                    print(f"  Gemini rate limit sementara, menunggu {jeda:.0f} detik.")
                    tidur(jeda)
                    sudah_menunggu = True
                    continue
                if salah.jenis == Jenis.RATE_LIMIT:
                    catat_cooldown("gemini", 0.25)
                    return None, "rate limit", notifikasi, None, percobaan
                alasan = salah.jenis.value.replace("_", " ")
                if salah.jenis == Jenis.MODEL_UNAVAILABLE:
                    break
                if salah.jenis in (Jenis.SERVER, Jenis.TIMEOUT, Jenis.BAD_RESPONSE) and _giliran + 1 < config.MAX_RETRY:
                    from .errors import jeda_sementara
                    tidur(jeda_sementara(_giliran))
                    continue
                break
    if terakhir is not None and "terlalu mirip" not in masalah_terakhir:
        return terakhir, "", notifikasi, f"Naskah Gemini dipakai walau belum ideal: {masalah_terakhir}", percobaan
    return None, alasan, notifikasi, None, percobaan


def _groq(instruksi, topik, label_berikut, hindari, pengirim, tidur, lanjutan=False) -> tuple[Naskah | None, str, list[str], int]:
    if config.SCRIPT_FALLBACK_PROVIDER not in ("groq", ""):
        return None, "fallback naskah bukan Groq", [], 0
    if not config.GROQ_API_KEY:
        print("  Groq dinonaktifkan: GROQ_API_KEY belum dikonfigurasi.")
        return None, "GROQ_API_KEY belum dikonfigurasi", [], 0
    if dalam_cooldown("groq"):
        print("  Groq sedang cooldown, tidak dipanggil.")
        return None, "cooldown", [], 0

    sudah_menunggu = False
    notifikasi = []
    prompt = instruksi + "\n\nBalas hanya JSON yang valid untuk skema naskah, termasuk array adegan."
    percobaan = 0
    for giliran in range(config.MAX_RETRY):
        percobaan += 1
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
            masalah = _masalah(naskah, label_berikut, lanjutan)
            bentrok = "" if topik else _mirip(naskah, hindari)
            if bentrok:
                masalah.append(f"terlalu mirip dengan {bentrok}")
            if masalah and giliran + 1 < config.MAX_RETRY:
                prompt = instruksi + "\n\nPerbaiki: " + "; ".join(masalah) + ". Balas hanya JSON."
                continue
            if masalah and "terlalu mirip" in "; ".join(masalah):
                return None, "topik terlalu mirip", notifikasi, percobaan
            if masalah:
                return naskah, "", [], percobaan
            print(f"  Model: {config.GROQ_MODEL}")
            return naskah, "", notifikasi, percobaan
        except (ValidationError, KeyError, json.JSONDecodeError, TypeError, ValueError) as e:
            print(f"  Groq gagal (respons tidak valid): {str(e)[:160]}")
            if giliran + 1 < config.MAX_RETRY:
                continue
            return None, "respons tidak valid", notifikasi, percobaan
        except Exception as e:
            salah = klasifikasi_exception("Groq", e)
            print(f"  Groq gagal ({salah.jenis.value}): {salah.pesan}")
            if salah.jenis == Jenis.INVALID_KEY:
                notifikasi.append("Konfigurasi Groq tidak valid. Periksa GROQ_API_KEY. Provider ini tidak dicoba lagi.")
                catat_cooldown("groq", 24)
                return None, "API key invalid", notifikasi, percobaan
            if salah.jenis in (Jenis.QUOTA, Jenis.BILLING):
                cooldown_kuota("groq")
                alasan = "quota limit" if salah.jenis == Jenis.QUOTA else "billing"
                return None, alasan, notifikasi, percobaan
            if salah.jenis == Jenis.RATE_LIMIT and not sudah_menunggu:
                from .errors import jeda_sementara
                jeda = min(salah.retry_after or jeda_sementara(0), 60)
                print(f"  Groq rate limit sementara, menunggu {jeda:.0f} detik.")
                tidur(jeda)
                sudah_menunggu = True
                continue
            if salah.jenis in (Jenis.SERVER, Jenis.TIMEOUT, Jenis.BAD_RESPONSE) and giliran + 1 < config.MAX_RETRY:
                from .errors import jeda_sementara
                tidur(jeda_sementara(giliran))
                continue
            return None, salah.jenis.value.replace("_", " "), notifikasi, percobaan
    return None, "gagal", notifikasi, percobaan


def buat_naskah(kategori, kategori_besok, label_berikut, topik=None, hindari=(), rekap_minggu=(), klien=None, pengirim=None, tidur=None, seri=None) -> HasilNaskah:
    from .template_naskah import template_lokal

    if not boleh_naskah_api() or mode() == "local_only":
        raise RuntimeError("Mode lokal tidak membuat naskah baru. Pakai --naskah pada aset yang sudah tersimpan.")

    pengirim = pengirim or requests.post
    tidur = tidur or time.sleep
    lanjutan = bool(seri)
    instruksi = _instruksi(kategori, kategori_besok, label_berikut, topik, list(hindari)[-40:], list(rekap_minggu), seri)
    konfigurasi = []
    alasan_gemini = ""
    naskah = None
    peringatan = None
    percobaan = 0

    if (klien is not None or config.GEMINI_API_KEY) and config.SCRIPT_PROVIDER in ("gemini", ""):
        if klien is None:
            from google import genai
            klien = genai.Client(api_key=config.GEMINI_API_KEY)
        naskah, alasan_gemini, notifikasi, peringatan, percobaan = _gemini(
            klien, instruksi, topik, label_berikut, hindari, tidur, lanjutan
        )
        konfigurasi.extend(notifikasi)
        if naskah is not None and peringatan is None:
            return HasilNaskah(naskah, "Gemini", config.GEMINI_MODEL, konfigurasi=konfigurasi, percobaan=percobaan)
        if naskah is not None and not config.TEXT_FALLBACK_ENABLED:
            return HasilNaskah(naskah, "Gemini", config.GEMINI_MODEL, peringatan=peringatan, konfigurasi=konfigurasi, percobaan=percobaan)
    else:
        alasan_gemini = "GEMINI_API_KEY belum dikonfigurasi" if config.SCRIPT_PROVIDER in ("gemini", "") else "provider naskah bukan Gemini"
        print(f"  Gemini dilewati: {alasan_gemini}.")

    if not config.TEXT_FALLBACK_ENABLED:
        if naskah is not None:
            return HasilNaskah(naskah, "Gemini", config.GEMINI_MODEL, peringatan=peringatan, konfigurasi=konfigurasi, percobaan=percobaan)
        raise RuntimeError(f"Gemini gagal ({alasan_gemini}) dan TEXT_FALLBACK_ENABLED=false.")

    groq_naskah, alasan_groq, notifikasi_groq, percobaan_groq = None, "tidak dicoba", [], 0
    if config.TEXT_FALLBACK_ENABLED:
        groq_naskah, alasan_groq, notifikasi_groq, percobaan_groq = _groq(
            instruksi, topik, label_berikut, hindari, pengirim, tidur, lanjutan
        )
        konfigurasi.extend(notifikasi_groq)
        percobaan += percobaan_groq
        if groq_naskah is not None and not _masalah(groq_naskah, label_berikut, lanjutan) and not ("" if topik else _mirip(groq_naskah, hindari)):
            return HasilNaskah(
                groq_naskah, "Groq", config.GROQ_MODEL,
                fallback_dari="Gemini", alasan=alasan_gemini or "naskah belum ideal",
                konfigurasi=konfigurasi, percobaan=percobaan,
            )

    if naskah is not None:
        catatan = peringatan or f"Naskah Gemini dipakai walau belum ideal: {alasan_groq}"
        return HasilNaskah(naskah, "Gemini", config.GEMINI_MODEL, peringatan=catatan, konfigurasi=konfigurasi, percobaan=percobaan)

    if not fallback_naskah_lokal():
        raise RuntimeError(f"Gemini gagal ({alasan_gemini}), Groq gagal ({alasan_groq}), dan template lokal dimatikan.")

    print(f"  Memakai template lokal. Gemini: {alasan_gemini}. Groq: {alasan_groq}.")
    lokal = template_lokal(kategori, kategori_besok, label_berikut, topik, hindari=hindari)
    alasan = alasan_gemini or "gagal"
    if alasan_groq and alasan_groq not in alasan:
        alasan = f"{alasan}, lalu Groq karena {alasan_groq}"
    ditolak = bool(not topik and _mirip(lokal, hindari))
    return HasilNaskah(
        lokal, "Template lokal", "template",
        fallback_dari="Gemini", alasan=alasan, konfigurasi=konfigurasi, percobaan=percobaan,
        ditolak=ditolak,
        peringatan="Template lokal terlalu mirip dengan riwayat." if ditolak else None,
    )
