import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from kpai import config
from kpai.caption import caption_menarik, deskripsi_youtube, judul_youtube, tagar_youtube
from kpai.errors import Jenis, klasifikasi_http, redaksi
from kpai.images import HARGA_PER_MEGAPIKSEL, buat_gambar, estimasi_usd
from kpai.laporan import laporan_selesai
from kpai.script_gen import _masalah, buat_naskah
from kpai.template_naskah import TOPIK, template_lokal


KAT = ("Luar Angkasa", "skenario luar angkasa")
BESOK = ("Fisika", "skenario fisika")


class Respon:
    def __init__(self, status=200, body=b"", teks="", json_body=None, headers=None):
        self.status_code = status
        self.content = body
        self.text = teks if teks or not body else body.decode("utf-8", "replace")
        self.headers = headers or {}
        self._json = json_body

    def json(self):
        if self._json is None:
            raise ValueError("bukan json")
        return self._json


def jpeg_bytes() -> bytes:
    img = Image.new("RGB", (320, 480), (12, 40, 90))
    px = img.load()
    for x in range(0, 320, 7):
        for y in range(0, 480, 5):
            px[x, y] = ((x * 3) % 255, (y * 2) % 255, 80)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


class KlienGemini:
    def __init__(self, efek):
        self.efek = list(efek)
        self.model = type("M", (), {})()
        self.model.panggilan = []
        self.models = self

    def generate_content(self, model, contents, config):
        self.model.panggilan.append(model)
        item = self.efek.pop(0)
        if isinstance(item, Exception):
            raise item
        return type("R", (), {"parsed": item, "text": item.model_dump_json()})()


class Kuota(Exception):
    def __init__(self):
        super().__init__("RESOURCE_EXHAUSTED quota exceeded")
        self.code = 429


def naskah_valid():
    return template_lokal(KAT, BESOK, "nanti siang")


class TestKlasifikasi(unittest.TestCase):
    def test_jenis_error_tidak_dicampur(self):
        self.assertEqual(klasifikasi_http("Gemini", 429, "too many requests").jenis, Jenis.RATE_LIMIT)
        self.assertEqual(klasifikasi_http("Gemini", 429, "quota exceeded").jenis, Jenis.QUOTA)
        self.assertEqual(klasifikasi_http("Gemini", 500, "rate limit mentioned but server down").jenis, Jenis.SERVER)
        self.assertEqual(klasifikasi_http("Gemini", 401, "API key not valid").jenis, Jenis.INVALID_KEY)
        self.assertEqual(klasifikasi_http("Gemini", 404, "model not found").jenis, Jenis.MODEL_UNAVAILABLE)
        self.assertEqual(klasifikasi_http("Gemini", 408, "request timeout").jenis, Jenis.TIMEOUT)
        self.assertEqual(klasifikasi_http("Cloudflare", 400, "daily free allocation exceeded").jenis, Jenis.QUOTA)
        self.assertEqual(klasifikasi_http("Gemini", 403, "You must enable billing on this project").jenis, Jenis.BILLING)

    def test_redaksi_tidak_menyimpan_kunci(self):
        with patch.object(config, "GROQ_API_KEY", "rahasia-groq-123456"):
            teks = redaksi("gagal rahasia-groq-123456 Bearer abc.def")
        self.assertNotIn("rahasia-groq-123456", teks)
        self.assertNotIn("abc.def", teks)


class TestTeks(unittest.TestCase):
    def setUp(self):
        self.patches = [
            patch.object(config, "GEMINI_API_KEY", "kunci-uji"),
            patch.object(config, "GEMINI_MODEL", "gemini-uji"),
            patch.object(config, "GEMINI_MODEL_CADANGAN", ["gemini-cadangan"]),
            patch.object(config, "TEXT_FALLBACK_ENABLED", True),
            patch.object(config, "GROQ_API_KEY", ""),
            patch.object(config, "GROQ_MODEL", "llama-3.3-70b-versatile"),
            patch.object(config, "COOLDOWN_FILE", Path(tempfile.mkdtemp()) / "cooldown.json"),
            patch.object(config, "PROVIDER_MODE", "free_safe"),
            patch.object(config, "SCRIPT_PROVIDER", "gemini"),
            patch.object(config, "SCRIPT_FALLBACK_PROVIDER", "groq"),
            patch.object(config, "SCRIPT_LOCAL_FALLBACK", True),
        ]
        for item in self.patches:
            item.start()
        self.addCleanup(lambda: [item.stop() for item in self.patches])

    def test_template_lolos_pemeriksaan(self):
        for nama in TOPIK:
            for label in ("nanti siang", "nanti sore", "nanti malam", "nanti larut", "besok"):
                naskah = template_lokal((nama, "cakupan"), ("Email & Chat Kerja", "email"), label)
                self.assertEqual(_masalah(naskah, label), [], nama)

    def test_gemini_sukses_tanpa_fallback(self):
        klien = KlienGemini([naskah_valid()])
        dipanggil = []

        def pengirim(*_a, **_k):
            dipanggil.append("groq")
            raise AssertionError("Groq tidak boleh dipanggil")

        hasil = buat_naskah(KAT, BESOK, "nanti siang", klien=klien, pengirim=pengirim, tidur=lambda _d: None)
        self.assertEqual(hasil.provider, "Gemini")
        self.assertIsNone(hasil.fallback_dari)
        self.assertEqual(dipanggil, [])
        self.assertEqual(klien.model.panggilan, ["gemini-uji"])

    def test_gemini_429_lalu_groq_sukses(self):
        klien = KlienGemini([Kuota()])
        config.GROQ_API_KEY = "kunci-groq-uji"
        jeda = []

        def pengirim(url, **_k):
            self.assertIn("api.groq.com/openai/v1/chat/completions", url)
            return Respon(200, json_body={"choices": [{"message": {"content": naskah_valid().model_dump_json()}}]})

        hasil = buat_naskah(KAT, BESOK, "nanti siang", klien=klien, pengirim=pengirim, tidur=jeda.append)
        self.assertEqual(hasil.provider, "Groq")
        self.assertEqual(hasil.fallback_dari, "Gemini")
        self.assertIn("quota limit", hasil.alasan)
        self.assertEqual(klien.model.panggilan, ["gemini-uji"])
        self.assertEqual(jeda, [])
        laporan = laporan_selesai(hasil, [])
        self.assertIn("Text: Groq (fallback dari Gemini karena quota limit).", laporan)
        self.assertNotIn("kunci-groq-uji", laporan)

    def test_caption_mengikuti_isi_video(self):
        naskah = naskah_valid()
        caption = caption_menarik(naskah, "Luar Angkasa")
        self.assertIn(naskah.hook, caption)
        self.assertIn(naskah.pertanyaan_komentar, caption)
        judul = judul_youtube(naskah, "Luar Angkasa")
        deskripsi = deskripsi_youtube(naskah, "Luar Angkasa")
        self.assertLessEqual(len(judul), 100)
        self.assertIn(naskah.hook, deskripsi)
        self.assertIn(naskah.penjelasan_ilmiah, deskripsi)
        self.assertIn("bantuan AI", deskripsi)
        self.assertIn("#Shorts", tagar_youtube("Luar Angkasa"))
        self.assertNotIn("tiktok", deskripsi.lower())


class TestGambar(unittest.TestCase):
    def setUp(self):
        self.patches = [
            patch.object(config, "CF_ACCOUNT_ID", "akun"),
            patch.object(config, "CF_API_TOKEN", "token-cf"),
            patch.object(config, "CF_IMAGE_MODELS", ["@cf/black-forest-labs/flux-1-schnell"]),
            patch.object(config, "CF_IMAGE_MODELS_HEMAT", ["@cf/black-forest-labs/flux-1-schnell"]),
            patch.object(config, "IMAGE_STYLE", "cinematic photo"),
            patch.object(config, "IMAGE_FALLBACK_ENABLED", False),
            patch.object(config, "FAL_KEY", ""),
            patch.object(config, "FAL_MODEL", "fal-ai/flux/schnell"),
            patch.object(config, "IMAGE_FALLBACK_MAX_COST_USD_PER_JOB", ""),
            patch.object(config, "PROVIDER_MODE", "free_safe"),
            patch.object(config, "FREE_ONLY", True),
            patch.object(config, "PAID_FALLBACK_ENABLED", False),
            patch.object(config, "HORDE_ENABLED", False),
            patch.object(config, "IMAGE_LOCAL_FALLBACK", True),
            patch.object(config, "IMAGE_DAILY_MAX", 20),
            patch.object(config, "KUOTA_FILE", Path(tempfile.mkdtemp()) / "kuota.json"),
            patch.object(config, "COOLDOWN_FILE", Path(tempfile.mkdtemp()) / "cooldown.json"),
            patch.object(config, "CACHE_DIR", Path(tempfile.mkdtemp()) / "cache"),
        ]
        for item in self.patches:
            item.start()
        self.addCleanup(lambda: [item.stop() for item in self.patches])

    def prompts(self):
        return {"hook": "person at a desk", "kerja": "hands on laptop", "trik": "smiling worker", "penutup": "morning office"}

    def test_estimasi_sesuai_harga_resmi(self):
        self.assertEqual(HARGA_PER_MEGAPIKSEL["fal-ai/flux/schnell"], 0.003)
        self.assertEqual(estimasi_usd("fal-ai/flux/schnell", 768, 1344, 1), 0.006)
        self.assertIsNone(estimasi_usd("model-tidak-dikenal", 768, 1344, 1))

    def test_cloudflare_gagal_fallback_berbayar_tetap_mati(self):
        url = []

        def pengirim(alamat, **_k):
            url.append(alamat)
            return Respon(500, teks="server error")

        folder = Path(tempfile.mkdtemp())
        with self.assertRaises(Exception) as ctx:
            buat_gambar(self.prompts(), folder, seed=1, pengirim=pengirim, pengambil=pengirim, tidur=lambda _d: None, folder_aset=folder / "kosong")
        self.assertEqual(type(ctx.exception).__name__, "NeedsReview")
        self.assertTrue(any("api.cloudflare.com" in item for item in url))
        self.assertFalse(any("fal.run" in item for item in url))
        self.assertEqual(list(folder.glob("gambar_*.jpg")), [])
        self.assertIn("IMAGE_FALLBACK_ENABLED=false", str(ctx.exception) + " ".join(ctx.exception.peringatan))

    def test_fallback_berbayar_hanya_saat_aktif_dan_biaya_cukup(self):
        config.FREE_ONLY = False
        config.PAID_FALLBACK_ENABLED = True
        config.PROVIDER_MODE = "auto_fallback"

        def jalan(aktif, batas):
            config.IMAGE_FALLBACK_ENABLED = aktif
            config.FAL_KEY = "fal-uji"
            config.IMAGE_FALLBACK_MAX_COST_USD_PER_JOB = batas
            url = []

            def pengirim(alamat, **_k):
                url.append(alamat)
                if "fal.run" in alamat:
                    return Respon(200, json_body={"images": [{"url": "https://cdn.example/a.jpg"}]}, teks="{}")
                return Respon(500, teks="server error")

            def pengambil(_alamat, **_k):
                return Respon(200, body=jpeg_bytes(), headers={"content-type": "image/jpeg"})

            folder = Path(tempfile.mkdtemp())
            return url, folder, pengirim, pengambil

        url, folder, pengirim, pengambil = jalan(True, "0.001")
        with self.assertRaises(Exception) as ctx:
            buat_gambar(self.prompts(), folder, 1, pengirim, pengambil, tidur=lambda _d: None, folder_aset=folder / "kosong")
        self.assertFalse(any("fal.run" in item for item in url))
        self.assertIn("melewati batas", " ".join(ctx.exception.peringatan))

        url, folder, pengirim, pengambil = jalan(True, "1")
        hasil = buat_gambar(self.prompts(), folder, 1, pengirim, pengambil, tidur=lambda _d: None, folder_aset=folder / "kosong")
        fal = [item for item in url if "fal.run" in item]
        self.assertEqual(len(fal), 4)
        self.assertEqual(set(hasil.gambar), {"hook", "kerja", "trik", "penutup"})
        self.assertAlmostEqual(sum(item.biaya_usd for item in hasil.catatan), 0.024)
        self.assertTrue(all(item.provider == "fal.ai" for item in hasil.catatan))
        for kunci in hasil.gambar:
            self.assertTrue((folder / f"gambar_{kunci}.jpg").is_file())
            self.assertGreater(hasil.gambar[kunci].width, 64)

    def test_kuota_cloudflare_habis_pindah_ke_horde(self):
        config.PROVIDER_MODE = "auto_fallback"
        config.HORDE_ENABLED = True
        url = []

        def pengirim(alamat, **_k):
            url.append(alamat)
            if "aihorde.net" in alamat:
                return Respon(202, json_body={"id": f"job-{len(url)}"}, teks="{}")
            return Respon(429, teks="you have used up your daily free allocation of 10,000 neurons")

        def pengambil(alamat, **_k):
            if "/generate/check/" in alamat:
                return Respon(200, json_body={"done": True, "is_possible": True, "faulted": False}, teks="{}")
            if "/generate/status/" in alamat:
                return Respon(200, json_body={"generations": [{"img": "https://r2.example/a.webp", "model": "AlbedoBase XL (SDXL)", "censored": False}]}, teks="{}")
            return Respon(200, body=jpeg_bytes(), headers={"content-type": "image/webp"})

        folder = Path(tempfile.mkdtemp())
        hasil = buat_gambar(self.prompts(), folder, 1, pengirim, pengambil, tidur=lambda _d: None, folder_aset=folder / "kosong")
        self.assertEqual(sum("api.cloudflare.com" in item for item in url), 1)
        self.assertEqual(sum("aihorde.net" in item for item in url), 4)
        self.assertFalse(any("fal.run" in item for item in url))
        self.assertTrue(all(item.provider == "AI Horde" for item in hasil.catatan))
        self.assertIn("Kuota harian Cloudflare habis", hasil.peringatan)

    def test_horde_disensor_tidak_dipakai(self):
        config.PROVIDER_MODE = "auto_fallback"
        config.HORDE_ENABLED = True
        nomor = []

        def pengirim(alamat, **_k):
            if "aihorde.net" in alamat:
                nomor.append(1)
                return Respon(202, json_body={"id": f"job-{len(nomor)}"}, teks="{}")
            return Respon(429, teks="daily free allocation exceeded")

        def pengambil(alamat, **_k):
            if "/generate/check/" in alamat:
                return Respon(200, json_body={"done": True}, teks="{}")
            return Respon(200, json_body={"generations": [{"img": "x", "censored": True}]}, teks="{}")

        folder = Path(tempfile.mkdtemp())
        with self.assertRaises(Exception) as ctx:
            buat_gambar(self.prompts(), folder, 1, pengirim, pengambil, tidur=lambda _d: None, folder_aset=folder / "kosong")
        self.assertEqual(type(ctx.exception).__name__, "NeedsReview")
        self.assertIn("AI Horde gagal untuk hook: bad_image", ctx.exception.peringatan)

    def test_semua_provider_gagal_tanpa_gradien(self):
        self.assertFalse(hasattr(__import__("kpai.images", fromlist=["images"]), "_cadangan"))
        config.FREE_ONLY = False
        config.PAID_FALLBACK_ENABLED = True
        config.PROVIDER_MODE = "auto_fallback"

        def pengirim(alamat, **_k):
            self.assertNotIn("pollinations", alamat)
            return Respon(500, teks="server error")

        folder = Path(tempfile.mkdtemp())
        config.IMAGE_FALLBACK_ENABLED = True
        config.FAL_KEY = "fal-uji"
        config.IMAGE_FALLBACK_MAX_COST_USD_PER_JOB = "1"
        config.FAL_MODEL = "model-tanpa-harga"

        with self.assertRaises(Exception) as ctx:
            buat_gambar(self.prompts(), folder, 1, pengirim, pengirim, tidur=lambda _d: None, folder_aset=folder / "tidak-ada")
        self.assertEqual(list(folder.glob("gambar_*.jpg")), [])
        self.assertIn("tidak diketahui", " ".join(ctx.exception.peringatan))
        self.assertIn("Gradien tidak dipakai", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
