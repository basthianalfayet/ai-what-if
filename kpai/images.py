import base64
import random
import time
import urllib.parse
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFilter

from . import config


def _cloudflare(model: str):
    def panggil(prompt: str, seed: int) -> Image.Image:
        url = f"https://api.cloudflare.com/client/v4/accounts/{config.CF_ACCOUNT_ID}/ai/run/{model}"
        headers = {"Authorization": f"Bearer {config.CF_API_TOKEN}"}
        if "flux-2" in model:
            # FLUX.2 hanya menerima multipart form.
            form = {"prompt": (None, prompt), "width": (None, "768"), "height": (None, "1344")}
            r = requests.post(url, headers=headers, files=form, timeout=180)
        elif "flux-1-schnell" in model:
            # Model ini menolak parameter selain prompt dan steps, dan hasilnya selalu persegi.
            r = requests.post(url, headers=headers, json={"prompt": prompt, "steps": 8}, timeout=180)
        else:
            r = requests.post(url, headers=headers, json={"prompt": prompt, "width": 768, "height": 1344}, timeout=180)
        if r.status_code != 200:
            raise RuntimeError(f"{r.status_code} {r.text[:150]}")
        if r.headers.get("content-type", "").startswith("image/"):
            return Image.open(BytesIO(r.content))
        return Image.open(BytesIO(base64.b64decode(r.json()["result"]["image"])))
    return panggil


def _pollinations(prompt: str, seed: int) -> Image.Image:
    url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt)
    r = requests.get(
        url,
        params={"width": 1080, "height": 1920, "nologo": "true", "model": "flux", "seed": seed},
        timeout=180,
    )
    r.raise_for_status()
    img = Image.open(BytesIO(r.content))
    # Potong pojok bawah tempat watermark.
    return img.crop((0, 0, img.width, int(img.height * 0.93)))


def _cadangan(seed: int, warna: tuple[int, int, int]) -> Image.Image:
    rnd = random.Random(seed)
    img = Image.new("RGB", (1080, 1920), tuple(c // 4 for c in warna))
    d = ImageDraw.Draw(img)
    for _ in range(7):
        r = rnd.randint(220, 520)
        x, y = rnd.randint(-100, 1180), rnd.randint(-100, 2020)
        c = tuple(min(255, int(v * rnd.uniform(0.5, 1.1))) for v in warna)
        d.ellipse((x - r, y - r, x + r, y + r), fill=c)
    return img.filter(ImageFilter.GaussianBlur(140))


def buat_gambar(prompts: dict[str, str], folder: Path, seed: int, warna_cadangan) -> dict[str, Image.Image]:
    ada_cf = bool(config.CF_ACCOUNT_ID and config.CF_API_TOKEN)
    if not ada_cf:
        print("  CF_ACCOUNT_ID/CF_API_TOKEN belum diisi, gambar AI hanya dari Pollinations (terbatas)")

    def penyedia_untuk(kunci):
        daftar = []
        if ada_cf and not kuota_cf_habis:
            for model in config.CF_IMAGE_MODELS if kunci == "hook" else config.CF_IMAGE_MODELS_HEMAT:
                daftar.append((f"Cloudflare {model.split('/')[-1]}", _cloudflare(model), 2))
        # Pollinations tanpa key cuma memberi ~1 gambar per beberapa menit, jadi hanya cadangan sekali coba.
        daftar.append(("Pollinations", _pollinations, 1))
        return daftar

    kuota_cf_habis = False
    hasil = {}
    for i, (kunci, prompt) in enumerate(prompts.items()):
        lengkap = f"{prompt}, {config.IMAGE_STYLE}"
        img = None
        for nama, fungsi, coba in penyedia_untuk(kunci):
            if kuota_cf_habis and nama.startswith("Cloudflare"):
                continue
            for percobaan in range(coba):
                try:
                    img = fungsi(lengkap, seed + i).convert("RGB")
                    print(f"  Gambar {kunci}: {nama} {img.width}x{img.height}")
                    break
                except Exception as e:
                    print(f"  Gambar {kunci} via {nama} gagal: {str(e)[:100]}")
                    if "daily free allocation" in str(e):
                        kuota_cf_habis = True
                        print("  Kuota harian Cloudflare habis, sisa gambar tidak lewat Cloudflare")
                        break
                    time.sleep(4)
            if img is not None:
                break
        if img is None:
            print(f"  Gambar {kunci}: pakai latar gradien")
            img = _cadangan(seed + i, warna_cadangan)
        img.save(folder / f"gambar_{kunci}.jpg", quality=92)
        hasil[kunci] = img
    return hasil
