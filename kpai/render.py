import math
import os
import random
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from . import config
from .script_gen import AJAKAN_SUBSCRIBE

W, H = 1080, 1920
M = 80
LEBAR_KARTU = W - 2 * M
SUBTITLE_Y = 1350
SKALA_LATAR = 1.2

TEMA = [
    dict(aksen=(255, 200, 40), bubble=(56, 120, 255)),
    dict(aksen=(120, 235, 190), bubble=(20, 150, 115)),
    dict(aksen=(255, 130, 175), bubble=(140, 80, 235)),
    dict(aksen=(255, 175, 60), bubble=(215, 80, 50)),
    dict(aksen=(110, 215, 255), bubble=(35, 115, 205)),
]
PUTIH = (255, 255, 255)
HITAM = (0, 0, 0)
TINTA = (20, 24, 33)
ABU = (112, 122, 140)
KARTU = (248, 249, 252)

KUNCI_GAMBAR = {"hook": "hook", "prompt": "kerja", "hasil": "kerja", "trik": "trik", "penutup": "penutup"}

_FONT_WINDOWS = {"ExtraBold": "segoeuib.ttf", "Bold": "segoeuib.ttf", "SemiBold": "seguisb.ttf"}
_FONT_LINUX = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
)


@lru_cache(maxsize=None)
def font(bobot: str, ukuran: int) -> ImageFont.FreeTypeFont:
    if config.FONT_FILE.exists():
        f = ImageFont.truetype(str(config.FONT_FILE), ukuran)
        try:
            f.set_variation_by_name(bobot)
        except (OSError, AttributeError):
            pass
        return f
    p = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / _FONT_WINDOWS.get(bobot, "segoeui.ttf")
    if p.exists():
        return ImageFont.truetype(str(p), ukuran)
    for cadangan in _FONT_LINUX:
        if Path(cadangan).exists():
            return ImageFont.truetype(cadangan, ukuran)
    return ImageFont.load_default(ukuran)


def _klem(x: float) -> float:
    return min(max(x, 0.0), 1.0)


def ease(x: float) -> float:
    return 1 - (1 - _klem(x)) ** 3


def ease_mantul(x: float) -> float:
    x = _klem(x)
    return 1 + 2.7 * (x - 1) ** 3 + 1.7 * (x - 1) ** 2


def bungkus(teks: str, f, lebar: int) -> list[str]:
    baris = []
    for paragraf in teks.split("\n"):
        if not paragraf.strip():
            baris.append("")
            continue
        sekarang = ""
        for kata in paragraf.split():
            coba = f"{sekarang} {kata}".strip()
            if f.getlength(coba) <= lebar:
                sekarang = coba
                continue
            if sekarang:
                baris.append(sekarang)
            while f.getlength(kata) > lebar:
                potong = len(kata)
                while potong > 1 and f.getlength(kata[:potong]) > lebar:
                    potong -= 1
                baris.append(kata[:potong])
                kata = kata[potong:]
            sekarang = kata
        baris.append(sekarang)
    return baris


def pas(teks, bobot, lebar, tinggi, besar, kecil, spasi=1.3):
    """Ukuran font terbesar yang membuat teks muat di kotak."""
    for ukuran in range(besar, kecil - 1, -2):
        f = font(bobot, ukuran)
        baris = bungkus(teks, f, lebar)
        tb = int(ukuran * spasi)
        if len(baris) * tb <= tinggi:
            return f, baris, tb
    f = font(bobot, kecil)
    tb = int(kecil * spasi)
    return f, bungkus(teks, f, lebar)[: max(1, tinggi // tb)], tb


def tulis_ketik(d, baris, f, x, y, tb, n, warna, warna_kurung=None):
    """Tulis n huruf pertama; teks [dalam kurung] diberi warna lain. Mengembalikan posisi ujung teks."""
    sisa, dalam, ujung = n, False, (x, y)
    for i, b in enumerate(baris):
        if sisa <= 0:
            break
        tampil = b[:sisa]
        sisa -= len(b) + 1
        cx, cy, run = x, y + i * tb, ""
        for ch in tampil:
            if warna_kurung and ch == "[" and not dalam:
                if run:
                    d.text((cx, cy), run, font=f, fill=warna)
                    cx += f.getlength(run)
                run, dalam = "", True
            run += ch
            if warna_kurung and ch == "]" and dalam:
                d.text((cx, cy), run, font=f, fill=warna_kurung)
                cx += f.getlength(run)
                run, dalam = "", False
        if run:
            d.text((cx, cy), run, font=f, fill=warna_kurung if dalam else warna)
            cx += f.getlength(run)
        ujung = (cx, cy)
    return ujung


def ukuran_pil(teks, f, pad_x=24, pad_y=12):
    return int(f.getlength(teks)) + pad_x * 2, f.size + pad_y * 2


def pil(d, x, y, teks, f, bg, fg, pad_x=24, pad_y=12):
    w, h = ukuran_pil(teks, f, pad_x, pad_y)
    d.rounded_rectangle((x, y, x + w, y + h), radius=h // 2, fill=bg)
    d.text((x + w / 2, y + h / 2), teks, font=f, fill=fg, anchor="mm")
    return w, h


def lapisan(w, h):
    return Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))


@lru_cache(maxsize=32)
def bayangan(w, h, radius):
    pad = 40
    img = lapisan(w + pad * 2, h + pad * 2)
    ImageDraw.Draw(img).rounded_rectangle((pad, pad + 14, pad + w, pad + h + 14), radius=radius, fill=(0, 0, 0, 150))
    return img.filter(ImageFilter.GaussianBlur(22))


def tempel(dst, lay, x, y, alpha=1.0):
    if alpha <= 0.01:
        return
    if alpha < 0.99:
        lay = lay.copy()
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * alpha)))
    dst.paste(lay, (int(x), int(y)), lay)


def mulai_ajakan(kata, durasi: float) -> float:
    for item in kata or []:
        if str(item.teks).casefold().startswith("subscribe"):
            return float(item.mulai)
    return max(0.0, float(durasi) - 2.0)


def saat_ajakan(kata, durasi: float, tl: float) -> bool:
    return tl >= mulai_ajakan(kata, durasi) - 1e-9


def potong_subtitle(kata) -> list[list[int]]:
    """Kelompokkan kata jadi potongan subtitle pendek (maks 3 kata / 20 huruf)."""
    potongan, sekarang = [], []
    for i, k in enumerate(kata):
        if sekarang:
            panjang = sum(len(kata[j].teks) + 1 for j in sekarang) + len(k.teks)
            jeda = k.mulai - kata[sekarang[-1]].selesai
            if len(sekarang) >= 3 or panjang > 20 or jeda > 0.3:
                potongan.append(sekarang)
                sekarang = []
        sekarang.append(i)
    if sekarang:
        potongan.append(sekarang)
    return potongan


class Renderer:
    def __init__(self, naskah, kategori, channel, gambar, indeks_tema, adegan, label_berikut):
        self.n = naskah
        self.whatif = bool(getattr(naskah, "adegan", None))
        self.kategori = kategori.upper()
        self.channel = channel
        self.t = TEMA[indeks_tema % len(TEMA)]
        self.adegan = adegan
        self.total = adegan[-1].mulai + adegan[-1].panjang
        self.label_berikut = label_berikut.upper()
        self._putih = Image.new("RGB", (W, H), PUTIH)
        self.kunci_gambar = {}
        for a in adegan:
            if a.nama in gambar:
                self.kunci_gambar[a.nama] = a.nama
            else:
                self.kunci_gambar[a.nama] = KUNCI_GAMBAR.get(a.nama, a.nama)

        self.latar = {k: self._siapkan_latar(img) for k, img in gambar.items()}
        rnd = random.Random(indeks_tema)
        self.gerak = {}
        for k in self.latar:
            z0, z1 = (1.0, 1.14) if rnd.random() < 0.65 else (1.14, 1.0)
            self.gerak[k] = (z0, z1, rnd.uniform(-1, 1), rnd.uniform(-0.6, 0.6))

        self.span = {}
        for a in adegan:
            k = self.kunci_gambar[a.nama]
            s0, s1 = self.span.get(k, (a.mulai, a.mulai + a.panjang))
            self.span[k] = (min(s0, a.mulai), max(s1, a.mulai + a.panjang))

        self.potongan = {a.nama: potong_subtitle(a.kata) for a in adegan}
        self.transisi = []
        for i, a in enumerate(adegan[1:], start=1):
            ganti_gambar = self.kunci_gambar[a.nama] != self.kunci_gambar[adegan[i - 1].nama]
            if self.whatif:
                jenis = "whoosh" if i == 1 else "pop"
            else:
                jenis = "whoosh" if ganti_gambar else "pop"
            self.transisi.append((a.mulai, jenis))

        self._siapkan_tata_letak()

    def _siapkan_latar(self, img):
        sw, sh = int(W * SKALA_LATAR), int(H * SKALA_LATAR)
        s = max(sw / img.width, sh / img.height)
        img = img.resize((math.ceil(img.width * s), math.ceil(img.height * s)), Image.LANCZOS)
        x, y = (img.width - sw) // 2, (img.height - sh) // 2
        img = ImageEnhance.Brightness(img.crop((x, y, x + sw, y + sh))).enhance(0.75)
        kolom = Image.new("L", (1, sh))
        for yy in range(sh):
            r = yy / (sh - 1)
            a = 0.12
            if r < 0.2:
                a += 0.5 * (1 - r / 0.2)
            elif r > 0.55:
                a += 0.7 * (r - 0.55) / 0.45
            kolom.putpixel((0, yy), int(255 * min(a, 0.85)))
        return Image.composite(Image.new("RGB", (sw, sh), HITAM), img, kolom.resize((sw, sh)))

    def _siapkan_tata_letak(self):
        n = self.n
        teks_hook = n.hook
        if self.whatif:
            for scene in n.adegan:
                if scene.id == "hook":
                    teks_hook = scene.narasi
                    break
        self.hook_layout = self._layout_hook(teks_hook)
        if not self.whatif:
            self.prompt_layout = pas(n.prompt, "Medium", LEBAR_KARTU - 80, 700, 46, 28, spasi=1.32)
            self.hasil_layout = pas(n.hasil, "Regular", LEBAR_KARTU - 80, 560, 44, 26, spasi=1.3)
            self.trik_layout = pas(f"\u201c{n.trik}\u201d", "Bold", LEBAR_KARTU - 120, 380, 56, 32, spasi=1.22)
            self.besok_layout = pas(n.topik_besok, "ExtraBold", LEBAR_KARTU - 80, 260, 64, 38, spasi=1.15)
            f_mini = font("Medium", 30)
            mini = bungkus(n.prompt.replace("\n", " "), f_mini, LEBAR_KARTU - 140 - 56)
            if len(mini) > 2:
                mini = [mini[0], mini[1].rstrip(" .,") + "..."]
            self.prompt_mini = mini
            return
        self.layar = {
            scene.id: pas(scene.judul_layar, "ExtraBold", LEBAR_KARTU - 80, 220, 60, 32, spasi=1.12)
            for scene in n.adegan
        }
        self.urutan = int(getattr(n, "urutan_seri", 1) or 1)
        self.berikut = (getattr(n, "topik_berikut", "") or "").strip() if self.urutan < 3 else ""
        self.tanya_layout = pas(n.pertanyaan_komentar, "Bold", LEBAR_KARTU - 100, 240, 42, 26, spasi=1.18)
        self.ajakan_layout = pas(AJAKAN_SUBSCRIBE, "Bold", LEBAR_KARTU - 100, 160, 40, 26, spasi=1.15)
        self.berikut_layout = (
            pas(self.berikut, "Medium", LEBAR_KARTU - 100, 140, 32, 22, spasi=1.15) if self.berikut else None
        )

    def _layout_hook(self, teks):
        f, baris, tb = pas(teks, "ExtraBold", LEBAR_KARTU, 640, 92, 42, spasi=1.12)
        posisi = []
        for i, b in enumerate(baris):
            x = M
            for kata in b.split():
                posisi.append((kata, x, i * tb))
                x += f.getlength(kata + " ")
        return f, posisi, len(baris) * tb

    def adegan_pada(self, t):
        for i in range(len(self.adegan) - 1, -1, -1):
            if t >= self.adegan[i].mulai - 1e-9:
                return i, self.adegan[i]
        return 0, self.adegan[0]

    def frame(self, t: float) -> Image.Image:
        i, a = self.adegan_pada(t)
        tl = t - a.mulai
        kunci = self.kunci_gambar[a.nama]
        gambar_baru = i == 0 or self.kunci_gambar[self.adegan[i - 1].nama] != kunci
        punch = 0.08 * (1 - ease(tl / 0.35)) if gambar_baru and tl < 0.35 else 0.0
        flash = 0.0 if self.whatif else (0.35 * (1 - tl / 0.16) if gambar_baru and i > 0 and tl < 0.16 else 0.0)

        img = self._latar(kunci, t, punch)
        d = ImageDraw.Draw(img)
        self._kepala(d)
        if self.whatif:
            self._whatif(img, d, a, tl)
        else:
            getattr(self, f"_{a.nama}")(img, d, a, tl)
        if a.nama != "hook":
            self._subtitle(d, a, tl)
        d.rectangle((0, 0, int(W * t / self.total), 9), fill=self.t["aksen"])
        if flash > 0:
            img = Image.blend(img, self._putih, flash)
        return img

    def _latar(self, kunci, t, punch):
        src = self.latar[kunci]
        sw, sh = src.size
        s0, s1 = self.span[kunci]
        p = _klem((t - s0) / max(s1 - s0, 0.01))
        p = p * p * (3 - 2 * p)
        z0, z1, dx, dy = self.gerak[kunci]
        z = (z0 + (z1 - z0) * p) * (1 + punch)
        cw, ch = sw / z, sh / z
        cx = sw / 2 + dx * (sw - cw) / 2 * (2 * p - 1)
        cy = sh / 2 + dy * (sh - ch) / 2 * (2 * p - 1)
        return src.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))

    def _kepala(self, d):
        d.text((M, 92), self.channel, font=font("ExtraBold", 36), fill=PUTIH)
        lebar_pil, _tinggi_pil = pil(d, M, 148, self.kategori, font("Bold", 24), self.t["aksen"], TINTA, pad_x=20, pad_y=10)
        if self.whatif and getattr(self, "urutan", 0) in (1, 2, 3):
            pil(
                d, M + lebar_pil + 12, 148, f"BAGIAN {self.urutan}/3",
                font("Bold", 24), self.t["bubble"], PUTIH, pad_x=16, pad_y=10,
            )
        if self.whatif:
            f = font("Bold", 22)
            teks = "SKENARIO FIKSI"
            w, _h = ukuran_pil(teks, f, 16, 8)
            pil(d, W - M - w, 148, teks, f, (20, 24, 33), PUTIH, 16, 8)

    def _whatif(self, img, d, a, tl):
        if a.nama == "hook":
            self._hook(img, d, a, tl)
            return
        if a.nama == "penutup":
            if saat_ajakan(a.kata, a.durasi, tl):
                self._kartu_subscribe(img, tl, mulai_ajakan(a.kata, a.durasi))
            else:
                self._kartu_singkat(img, tl, self.tanya_layout, "MENURUTMU")
            return
        layout = self.layar.get(a.nama)
        if layout:
            self._kartu_singkat(img, tl, layout, "YANG TERJADI" if a.nama == "awal" else "KONSEKUENSINYA")

    def _kartu_singkat(self, img, tl, layout, label):
        e = ease(tl / 0.4)
        f, baris, tb = layout
        tinggi = 88 + len(baris) * tb + 36
        lay = lapisan(LEBAR_KARTU, tinggi)
        ld = ImageDraw.Draw(lay)
        ld.rounded_rectangle((0, 0, lay.width - 1, lay.height - 1), radius=28, fill=(12, 15, 24, 214))
        ld.text((36, 28), label, font=font("Bold", 24), fill=self.t["aksen"])
        for i, b in enumerate(baris):
            ld.text((36, 78 + i * tb), b, font=f, fill=PUTIH)
        self._kartu(img, lay, 430, e)

    def _kartu_subscribe(self, img, tl, mulai):
        e = ease((tl - mulai) / 0.3)
        f, baris, tb = self.ajakan_layout
        tinggi = 88 + len(baris) * tb + 28
        if self.berikut_layout:
            _fb, baris_b, tb_b = self.berikut_layout
            tinggi += 36 + len(baris_b) * tb_b
        tinggi += 20
        lay = lapisan(LEBAR_KARTU, tinggi)
        ld = ImageDraw.Draw(lay)
        ld.rounded_rectangle((0, 0, lay.width - 1, lay.height - 1), radius=28, fill=(12, 15, 24, 214))
        ld.text((36, 28), "SUBSCRIBE", font=font("Bold", 24), fill=self.t["aksen"])
        y = 78
        for i, b in enumerate(baris):
            ld.text((36, y + i * tb), b, font=f, fill=PUTIH)
        y += len(baris) * tb + 16
        if self.berikut_layout:
            fb, baris_b, tb_b = self.berikut_layout
            ld.text((36, y), "Berikutnya", font=font("Bold", 22), fill=self.t["aksen"])
            y += 34
            for i, b in enumerate(baris_b):
                ld.text((36, y + i * tb_b), b, font=fb, fill=PUTIH)
        self._kartu(img, lay, 430, e)

    def _kartu(self, img, lay, y_akhir, e, radius=34):
        y = y_akhir + (1 - e) * 140
        tempel(img, bayangan(lay.width, lay.height, radius), M - 40, y - 40, e * 0.9)
        tempel(img, lay, M, y, e)

    def _hook(self, img, d, a, tl):
        f, posisi, tinggi = self.hook_layout
        y0 = 780 - tinggi // 2
        n_kata, n_tts = len(posisi), len(a.kata)
        muncul = [
            a.kata[min(n_tts - 1, int(i * n_tts / n_kata))].mulai - 0.05 if n_tts else i * 0.25
            for i in range(n_kata)
        ]
        muncul[0] = 0.0
        terlihat = [i for i in range(n_kata) if muncul[i] <= tl]
        for i in terlihat:
            kata, x, y = posisi[i]
            dy = (1 - ease_mantul((tl - muncul[i]) / 0.22)) * 50
            warna = self.t["aksen"] if i == terlihat[-1] and i < n_kata - 1 else PUTIH
            d.text((x, y0 + y + dy), kata, font=f, fill=warna, stroke_width=4, stroke_fill=HITAM)
        lebar = 220 * ease((tl - 0.1) / 0.5)
        if lebar > 4:
            d.rounded_rectangle((M, y0 + tinggi + 34, M + lebar, y0 + tinggi + 50), radius=8, fill=self.t["aksen"])

    def _prompt(self, img, d, a, tl):
        e = ease(tl / 0.35)
        pil(d, M - (1 - e) * 400, 300, "PROMPT BUAT DICONTEK", font("ExtraBold", 28), self.t["aksen"], TINTA)
        f, baris, tb = self.prompt_layout
        lay = lapisan(LEBAR_KARTU, len(baris) * tb + 90)
        ld = ImageDraw.Draw(lay)
        ld.rounded_rectangle((0, 0, lay.width - 1, lay.height - 1), radius=34, fill=(12, 15, 24, 238),
                             outline=self.t["aksen"], width=3)
        total = sum(len(b) + 1 for b in baris)
        n = int(total * _klem((tl - 0.2) / (0.72 * a.durasi)))
        ux, uy = tulis_ketik(ld, baris, f, 40, 42, tb, n, PUTIH, self.t["aksen"])
        if n < total or int(tl * 2.4) % 2 == 0:
            ld.rectangle((ux + 4, uy + 8, ux + 18, uy + f.size + 6), fill=self.t["aksen"])
        self._kartu(img, lay, 385, e)

    def _hasil(self, img, d, a, tl):
        e1 = ease(tl / 0.3)
        f_mini = font("Medium", 30)
        bw, bh = LEBAR_KARTU - 140, 36 + len(self.prompt_mini) * 42
        mini = lapisan(bw, bh)
        md = ImageDraw.Draw(mini)
        md.rounded_rectangle((0, 0, bw - 1, bh - 1), radius=28, fill=self.t["bubble"] + (255,))
        for i, b in enumerate(self.prompt_mini):
            md.text((28, 16 + i * 42), b, font=f_mini, fill=PUTIH)
        tempel(img, mini, W - M - bw + (1 - e1) * 220, 300, e1)

        f, baris, tb = self.hasil_layout
        lay = lapisan(LEBAR_KARTU, 110 + len(baris) * tb + 40)
        ld = ImageDraw.Draw(lay)
        ld.rounded_rectangle((0, 0, lay.width - 1, lay.height - 1), radius=34, fill=KARTU + (255,))
        ld.ellipse((36, 28, 88, 80), fill=self.t["bubble"])
        ld.text((62, 54), "AI", font=font("ExtraBold", 22), fill=PUTIH, anchor="mm")
        f_judul = font("ExtraBold", 32)
        ld.text((106, 36), "Jawaban AI", font=f_judul, fill=TINTA)
        total = sum(len(b) + 1 for b in baris)
        progres = (tl - 0.4) / (0.8 * a.durasi)
        if progres < 1:
            x0 = 106 + f_judul.getlength("Jawaban AI") + 22
            for k in range(3):
                r = 5 + 3 * (math.sin(tl * 9 - k * 0.9) + 1) / 2
                cx = x0 + k * 22
                ld.ellipse((cx - r, 56 - r, cx + r, 56 + r), fill=ABU)
        tulis_ketik(ld, baris, f, 40, 110, tb, int(total * _klem(progres)), TINTA)
        self._kartu(img, lay, 300 + bh + 30, ease((tl - 0.15) / 0.35))

    def _trik(self, img, d, a, tl):
        e = ease(tl / 0.35)
        pil(d, M - (1 - e) * 400, 380, "+ TRIK TAMBAHAN", font("ExtraBold", 30), self.t["aksen"], TINTA)
        f, baris, tb = self.trik_layout
        isi = len(baris) * tb + 50
        lay = lapisan(LEBAR_KARTU, 110 + isi + 40)
        ld = ImageDraw.Draw(lay)
        ld.rounded_rectangle((0, 0, lay.width - 1, lay.height - 1), radius=34, fill=KARTU + (255,))
        ld.text((40, 38), "Tempel di akhir prompt:", font=font("SemiBold", 34), fill=ABU)
        lebar = (LEBAR_KARTU - 60) * ease((tl - 0.35) / 0.6)
        if lebar > 30:
            ld.rounded_rectangle((30, 100, 30 + lebar, 100 + isi), radius=24, fill=self.t["aksen"])
        for i, b in enumerate(baris):
            ld.text((60, 124 + i * tb), b, font=f, fill=TINTA)
        self._kartu(img, lay, 470, e)

    def _penutup(self, img, d, a, tl):
        cx = W // 2
        atas = 300 - (1 - ease(tl / 0.3)) * 80 + math.sin(tl * 4) * 6
        d.polygon([(cx - 42, atas), (cx + 42, atas), (cx + 42, atas + 112), (cx, atas + 82), (cx - 42, atas + 112)],
                  fill=self.t["aksen"])
        f_judul = font("ExtraBold", 86)
        teks = "Simpan video ini"
        skala = ease_mantul(tl / 0.35)
        d.text((cx, 500 + (1 - skala) * 40), teks, font=f_judul, fill=PUTIH, anchor="mm", stroke_width=3, stroke_fill=HITAM)

        f, baris, tb = self.besok_layout
        lay = lapisan(LEBAR_KARTU, 120 + len(baris) * tb + 40)
        ld = ImageDraw.Draw(lay)
        ld.rounded_rectangle((0, 0, lay.width - 1, lay.height - 1), radius=34, fill=KARTU + (255,))
        pil(ld, 40, 32, self.label_berikut, font("ExtraBold", 28), self.t["bubble"], PUTIH)
        for i, b in enumerate(baris):
            ld.text((40, 116 + i * tb), b, font=f, fill=TINTA)
        y_kartu = 620
        self._kartu(img, lay, y_kartu, ease((tl - 0.25) / 0.4))

        e3 = ease((tl - 0.6) / 0.4)
        if e3 > 0:
            denyut = (math.sin(tl * 6) + 1) / 2 * 0.35
            bg = tuple(int(c + (255 - c) * denyut) for c in self.t["aksen"])
            f_follow = font("ExtraBold", 40)
            teks = f"Follow @{self.channel}"
            w, h = ukuran_pil(teks, f_follow, 34, 18)
            pl = lapisan(w, h)
            pil(ImageDraw.Draw(pl), 0, 0, teks, f_follow, bg, TINTA, 34, 18)
            tempel(img, pl, (W - w) / 2, y_kartu + lay.height + 70 + (1 - e3) * 60, e3)

    def _subtitle(self, d, a, tl):
        kata = a.kata
        aktif = None
        for i, k in enumerate(kata):
            if k.mulai <= tl:
                aktif = i
            else:
                break
        if aktif is None:
            return
        potong = next(p for p in self.potongan[a.nama] if aktif in p)
        if aktif == potong[-1] and tl > kata[aktif].selesai + 0.5:
            return

        teks = [kata[j].teks.upper() for j in potong]
        for ukuran in range(68, 38, -4):
            f = font("ExtraBold", ukuran)
            spasi = f.getlength(" ") + 34
            lebar = sum(f.getlength(x) for x in teks) + spasi * (len(teks) - 1)
            if lebar <= W - 160:
                break
        x = (W - lebar) / 2
        pop = ease_mantul((tl - kata[aktif].mulai) / 0.15)
        for t, j in zip(teks, potong):
            if j == aktif:
                l, atas, r, bawah = d.textbbox((x, SUBTITLE_Y), t, font=f)
                pad = 6 + 10 * pop
                d.rounded_rectangle((l - pad, atas - pad * 0.7, r + pad, bawah + pad * 0.7), radius=16, fill=self.t["aksen"])
                d.text((x, SUBTITLE_Y), t, font=f, fill=TINTA)
            else:
                d.text((x, SUBTITLE_Y), t, font=f, fill=PUTIH, stroke_width=6, stroke_fill=HITAM)
            x += f.getlength(t) + spasi
