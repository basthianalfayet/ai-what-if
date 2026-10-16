import math
import time
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

from . import config
from .errors import Jenis, NeedsReview, ProviderError, dari_response, klasifikasi_exception

LEBAR_FAL = 768
TINGGI_FAL = 1344
# Harga resmi fal.ai untuk fal-ai/flux/schnell: $0.003 per megapiksel, dibulatkan ke atas.
HARGA_PER_MEGAPIKSEL = {"fal-ai/flux/schnell": 0.003}
NAMA_CF = "Cloudflare Workers AI"
NAMA_FAL = "fal.ai"
NAMA_HORDE = "AI Horde"
NAMA_LOKAL = "Aset lokal"
URL_HORDE = "https://aihorde.net/api/v2"
# Ukuran potret standar SDXL (~1 MP); di atas 1024x1024 pengguna anonim bisa diminta kudos di muka.
LEBAR_HORDE = 832
TINGGI_HORDE = 1216
NEGATIF_HORDE = "text, letters, watermark, logo, blurry, deformed, extra fingers, bad hands, nsfw"


@dataclass
class CatatanGambar:
    scene: str
    provider: str
    model: str
    status: str
    biaya_usd: float | None = None


@dataclass
class HasilGambar:
    gambar: dict
    catatan: list
    peringatan: list
    konfigurasi: list


def estimasi_usd(model: str, lebar: int, tinggi: int, jumlah: int) -> float | None:
    harga = HARGA_PER_MEGAPIKSEL.get(model)
    if harga is None or jumlah < 1:
        return None
    megapiksel = max(1, math.ceil((lebar * tinggi) / 1_000_000))
    return round(harga * megapiksel * jumlah, 6)


def _batas_biaya() -> float | None:
    mentah = config.IMAGE_FALLBACK_MAX_COST_USD_PER_JOB.strip()
    if not mentah:
        return None
    try:
        nilai = float(mentah)
    except ValueError:
        return None
    if nilai < 0:
        return None
    return nilai


def _validasi(img: Image.Image) -> Image.Image:
    img = img.convert("RGB")
    if img.width < 64 or img.height < 64:
        raise ProviderError(Jenis.BAD_IMAGE, "gambar", "Gambar kosong atau terlalu kecil")
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=92)
    if buf.tell() < 80:
        raise ProviderError(Jenis.BAD_IMAGE, "gambar", "File gambar rusak atau kosong")
    buf.seek(0)
    cek = Image.open(buf)
    cek.load()
    return cek.convert("RGB")


def _bytes_ke_gambar(data: bytes, provider: str) -> Image.Image:
    if not data:
        raise ProviderError(Jenis.BAD_IMAGE, provider, "Respons gambar kosong")
    try:
        return _validasi(Image.open(BytesIO(data)))
    except ProviderError:
        raise
    except Exception as e:
        raise ProviderError(Jenis.BAD_IMAGE, provider, f"Gambar tidak bisa dibaca: {e}") from None


def _cloudflare(model: str, prompt: str, pengirim) -> Image.Image:
    url = f"https://api.cloudflare.com/client/v4/accounts/{config.CF_ACCOUNT_ID}/ai/run/{model}"
    headers = {"Authorization": f"Bearer {config.CF_API_TOKEN}"}
    if "flux-2" in model:
        berkas = {"prompt": (None, prompt), "width": (None, "768"), "height": (None, "1344")}
        respon = pengirim(url, headers=headers, files=berkas, timeout=180)
    elif "flux-1-schnell" in model:
        respon = pengirim(url, headers=headers, json={"prompt": prompt, "steps": 8}, timeout=180)
    else:
        respon = pengirim(url, headers=headers, json={"prompt": prompt, "width": 768, "height": 1344}, timeout=180)
    salah = dari_response(NAMA_CF, respon)
    if salah:
        raise salah
    jenis = (respon.headers.get("content-type") or "") if hasattr(respon, "headers") else ""
    if jenis.startswith("image/"):
        return _bytes_ke_gambar(respon.content, NAMA_CF)
    import base64
    try:
        mentah = base64.b64decode(respon.json()["result"]["image"])
    except Exception as e:
        raise ProviderError(Jenis.BAD_IMAGE, NAMA_CF, f"Respons gambar tidak lengkap: {e}") from None
    return _bytes_ke_gambar(mentah, NAMA_CF)


def _fal(model: str, prompt: str, pengirim, pengambil) -> Image.Image:
    respon = pengirim(
        f"https://fal.run/{model}",
        headers={"Authorization": f"Key {config.FAL_KEY}", "Content-Type": "application/json"},
        json={
            "prompt": prompt,
            "image_size": {"width": LEBAR_FAL, "height": TINGGI_FAL},
            "num_images": 1,
            "num_inference_steps": 4,
            "output_format": "jpeg",
            "enable_safety_checker": True,
        },
        timeout=180,
    )
    salah = dari_response(NAMA_FAL, respon)
    if salah:
        raise salah
    try:
        url = respon.json()["images"][0]["url"]
    except Exception as e:
        raise ProviderError(Jenis.BAD_IMAGE, NAMA_FAL, f"Respons fal.ai tidak berisi gambar: {e}") from None
    if not url:
        raise ProviderError(Jenis.BAD_IMAGE, NAMA_FAL, "URL gambar fal.ai kosong")
    unduh = pengambil(url, timeout=180)
    salah = dari_response(NAMA_FAL, unduh)
    if salah:
        raise salah
    return _bytes_ke_gambar(unduh.content, NAMA_FAL)


def _header_horde() -> dict:
    return {"apikey": config.HORDE_API_KEY, "Client-Agent": "KerjaPakaiAI:1.0:github.com/basthianalfayet"}


def _horde_kirim(prompt: str, pengirim) -> str:
    respon = pengirim(
        f"{URL_HORDE}/generate/async",
        headers=_header_horde(),
        json={
            "prompt": f"{prompt} ### {NEGATIF_HORDE}",
            "params": {
                "width": LEBAR_HORDE,
                "height": TINGGI_HORDE,
                "steps": 25,
                "cfg_scale": 6,
                "sampler_name": "k_dpmpp_2m",
                "karras": True,
                "n": 1,
            },
            "models": config.HORDE_MODELS,
            "nsfw": False,
            "censor_nsfw": True,
            "r2": True,
            "shared": False,
            "slow_workers": True,
        },
        timeout=60,
    )
    salah = dari_response(NAMA_HORDE, respon)
    if salah:
        raise salah
    try:
        return respon.json()["id"]
    except Exception as e:
        raise ProviderError(Jenis.PERMANENT, NAMA_HORDE, f"Respons AI Horde tanpa id: {e}") from None


def _horde_ambil(id_job: str, pengambil) -> tuple[Image.Image, str]:
    respon = pengambil(f"{URL_HORDE}/generate/status/{id_job}", headers=_header_horde(), timeout=60)
    salah = dari_response(NAMA_HORDE, respon)
    if salah:
        raise salah
    try:
        hasil = respon.json()["generations"][0]
    except Exception as e:
        raise ProviderError(Jenis.BAD_IMAGE, NAMA_HORDE, f"Respons AI Horde tanpa gambar: {e}") from None
    if hasil.get("censored"):
        raise ProviderError(Jenis.BAD_IMAGE, NAMA_HORDE, "Gambar disensor filter AI Horde")
    unduh = pengambil(hasil["img"], timeout=120)
    salah = dari_response(NAMA_HORDE, unduh)
    if salah:
        raise salah
    return _bytes_ke_gambar(unduh.content, NAMA_HORDE), hasil.get("model") or "?"


def _horde(gagal: list, pengirim, pengambil, tidur) -> tuple[dict, list[str]]:
    """Kirim semua scene sekaligus ke antrean, lalu tunggu bersamaan sampai batas waktu."""
    hasil, masalah = {}, []
    antre = list(gagal)
    aktif = {}
    batas = time.monotonic() + config.HORDE_MAX_WAIT_DETIK
    while (antre or aktif) and time.monotonic() < batas:
        while antre:
            kunci, lengkap = antre[0]
            try:
                aktif[_horde_kirim(lengkap, pengirim)] = kunci
                antre.pop(0)
            except Exception as e:
                salah = klasifikasi_exception(NAMA_HORDE, e)
                if salah.jenis == Jenis.RATE_LIMIT and aktif:
                    break
                print(f"  {NAMA_HORDE} gagal untuk {kunci} ({salah.jenis.value}): {salah.pesan}")
                masalah.append(f"{NAMA_HORDE} gagal untuk {kunci}: {salah.jenis.value}")
                antre.pop(0)
        if not aktif:
            break
        tidur(8)
        for id_job, kunci in list(aktif.items()):
            try:
                respon = pengambil(f"{URL_HORDE}/generate/check/{id_job}", headers=_header_horde(), timeout=30)
                salah = dari_response(NAMA_HORDE, respon)
                if salah:
                    if salah.jenis in (Jenis.RATE_LIMIT, Jenis.SERVER, Jenis.TIMEOUT):
                        continue
                    raise salah
                status = respon.json()
                if status.get("faulted") or status.get("is_possible") is False:
                    raise ProviderError(Jenis.MODEL_UNAVAILABLE, NAMA_HORDE, "tidak ada worker yang sanggup mengerjakan")
                if not status.get("done"):
                    continue
                img, model = _horde_ambil(id_job, pengambil)
                hasil[kunci] = (img, model)
                print(f"  Gambar {kunci}: {NAMA_HORDE} {model} {img.width}x{img.height}")
            except Exception as e:
                salah = klasifikasi_exception(NAMA_HORDE, e)
                print(f"  {NAMA_HORDE} gagal untuk {kunci} ({salah.jenis.value}): {salah.pesan}")
                masalah.append(f"{NAMA_HORDE} gagal untuk {kunci}: {salah.jenis.value}")
            del aktif[id_job]
    for kunci in list(aktif.values()) + [k for k, _ in antre]:
        masalah.append(f"{NAMA_HORDE} melewati batas tunggu {config.HORDE_MAX_WAIT_DETIK} detik untuk {kunci}")
    for id_job in aktif:
        try:
            requests.delete(f"{URL_HORDE}/generate/status/{id_job}", headers=_header_horde(), timeout=15)
        except requests.RequestException:
            pass
    return hasil, masalah


def _aset_lokal(kunci: str, folder: Path) -> Image.Image | None:
    if not folder.exists():
        return None
    for ekstensi in (".jpg", ".jpeg", ".png", ".webp"):
        path = folder / f"{kunci}{ekstensi}"
        if not path.is_file():
            continue
        try:
            return _validasi(Image.open(path))
        except ProviderError:
            return None
    return None


def _boleh_fal(jumlah: int) -> tuple[bool, str, float | None]:
    if not config.IMAGE_FALLBACK_ENABLED:
        return False, "IMAGE_FALLBACK_ENABLED=false", None
    if not config.FAL_KEY:
        return False, "FAL_KEY belum dikonfigurasi, fal.ai dinonaktifkan", None
    estimasi = estimasi_usd(config.FAL_MODEL, LEBAR_FAL, TINGGI_FAL, jumlah)
    if estimasi is None:
        return False, f"biaya model {config.FAL_MODEL} tidak diketahui, fallback berbayar dihentikan", None
    batas = _batas_biaya()
    if batas is None:
        return False, "IMAGE_FALLBACK_MAX_COST_USD_PER_JOB belum diisi atau tidak valid, fallback berbayar dihentikan", None
    if estimasi > batas:
        return False, f"estimasi ${estimasi:.4f} melewati batas ${batas:.4f}", estimasi
    return True, "", estimasi


def _coba(nama: str, fungsi, tidur, boleh_ulang: bool):
    try:
        return fungsi(), None
    except Exception as e:
        salah = klasifikasi_exception(nama, e)
        print(f"  {nama} gagal ({salah.jenis.value}): {salah.pesan}")
        if boleh_ulang and salah.jenis in (Jenis.TIMEOUT, Jenis.SERVER):
            tidur(2)
            try:
                return fungsi(), None
            except Exception as e2:
                return None, klasifikasi_exception(nama, e2)
        return None, salah


def buat_gambar(prompts: dict[str, str], folder: Path, seed: int, pengirim=None, pengambil=None, tidur=None, folder_aset=None):
    del seed  # pemanggilan gambar tidak memakai seed ulang untuk request yang sama
    pengirim = pengirim or requests.post
    pengambil = pengambil or requests.get
    tidur = tidur or time.sleep
    folder_aset = config.FALLBACK_DIR if folder_aset is None else folder_aset
    peringatan, konfigurasi = [], []
    hasil, catatan = {}, []
    gagal = []
    hentikan_cf = not (config.CF_ACCOUNT_ID and config.CF_API_TOKEN)
    if hentikan_cf:
        pesan = "Cloudflare dinonaktifkan: CF_ACCOUNT_ID atau CF_API_TOKEN belum dikonfigurasi."
        print(f"  {pesan}")
        peringatan.append(pesan)

    for kunci, prompt in prompts.items():
        lengkap = f"{prompt}, {config.IMAGE_STYLE}"
        if hentikan_cf:
            gagal.append((kunci, lengkap))
            continue
        model_daftar = config.CF_IMAGE_MODELS if kunci == "hook" else config.CF_IMAGE_MODELS_HEMAT
        img, meta, salah = None, None, None
        for model in model_daftar:
            def panggil(model=model, lengkap=lengkap):
                return _cloudflare(model, lengkap, pengirim)
            img, salah = _coba(NAMA_CF, panggil, tidur, boleh_ulang=True)
            if img is not None:
                meta = CatatanGambar(kunci, NAMA_CF, model, "ok", 0.0)
                print(f"  Gambar {kunci}: {NAMA_CF} {model} {img.width}x{img.height}")
                break
            if salah and salah.jenis == Jenis.QUOTA:
                if "Kuota harian Cloudflare habis" not in peringatan:
                    peringatan.append("Kuota harian Cloudflare habis")
                hentikan_cf = True
                break
            if salah and salah.jenis == Jenis.INVALID_KEY:
                konfigurasi.append("Konfigurasi Cloudflare tidak valid. Periksa CF_API_TOKEN. Provider ini tidak dicoba lagi.")
                hentikan_cf = True
                break
            if salah and salah.jenis == Jenis.RATE_LIMIT:
                jeda = min(salah.retry_after or 3, 60)
                print(f"  Cloudflare rate limit sementara, menunggu {jeda:.0f} detik sekali.")
                tidur(jeda)
                img, salah = _coba(NAMA_CF, panggil, tidur, boleh_ulang=False)
                if img is not None:
                    meta = CatatanGambar(kunci, NAMA_CF, model, "ok", 0.0)
                    break
                hentikan_cf = True
                break
        if img is not None:
            hasil[kunci] = img
            catatan.append(meta)
        else:
            gagal.append((kunci, lengkap))

    if gagal and config.HORDE_ENABLED:
        print(f"  {len(gagal)} scene dicoba lewat {NAMA_HORDE} (gratis, bisa antre beberapa menit)...")
        dari_horde, masalah = _horde(gagal, pengirim, pengambil, tidur)
        for kunci, (img, model) in dari_horde.items():
            hasil[kunci] = img
            catatan.append(CatatanGambar(kunci, NAMA_HORDE, model, "ok", 0.0))
        peringatan.extend(masalah)
        gagal = [(kunci, lengkap) for kunci, lengkap in gagal if kunci not in hasil]

    if gagal:
        boleh, alasan, estimasi = _boleh_fal(len(gagal))
        biaya_scene = (estimasi / len(gagal)) if boleh and estimasi is not None else None
        if not boleh:
            print(f"  fal.ai tidak dipanggil: {alasan}")
            peringatan.append(f"fal.ai tidak dipanggil: {alasan}")
        sisa = []
        for kunci, lengkap in gagal:
            if not boleh:
                sisa.append((kunci, lengkap))
                continue
            def panggil_fal(lengkap=lengkap):
                return _fal(config.FAL_MODEL, lengkap, pengirim, pengambil)
            img, salah = _coba(NAMA_FAL, panggil_fal, tidur, boleh_ulang=False)
            if img is not None:
                hasil[kunci] = img
                catatan.append(CatatanGambar(kunci, NAMA_FAL, config.FAL_MODEL, "ok", biaya_scene))
                print(f"  Gambar {kunci}: {NAMA_FAL} {config.FAL_MODEL} biaya ${biaya_scene:.4f}")
                continue
            if salah and salah.jenis == Jenis.INVALID_KEY:
                konfigurasi.append("Konfigurasi fal.ai tidak valid. Periksa FAL_KEY. Provider ini tidak dicoba lagi.")
                boleh = False
            sisa.append((kunci, lengkap))
        for kunci, _lengkap in sisa:
            if kunci in hasil:
                continue
            lokal = _aset_lokal(kunci, folder_aset)
            if lokal is not None:
                hasil[kunci] = lokal
                catatan.append(CatatanGambar(kunci, NAMA_LOKAL, kunci, "ok", 0.0))
                print(f"  Gambar {kunci}: {NAMA_LOKAL}")
                peringatan.append(f"Gambar {kunci} dari aset lokal")

    kurang = [kunci for kunci in prompts if kunci not in hasil]
    if kurang:
        alasan = (
            f"scene {', '.join(kurang)} tidak punya gambar yang lolos pemeriksaan. "
            "Gradien tidak dipakai sebagai pengganti."
        )
        raise NeedsReview(alasan, peringatan, konfigurasi)

    for kunci, img in hasil.items():
        path = folder / f"gambar_{kunci}.jpg"
        img.save(path, format="JPEG", quality=92)
        hasil[kunci] = _validasi(Image.open(path))
    return HasilGambar(hasil, catatan, peringatan, konfigurasi)
