import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from kpai import config, history
from kpai.caption import simpan_metadata
from kpai.errors import NeedsReview
from kpai.images import buat_gambar
from kpai.jalan import jalankan_berurutan
from kpai.kualitas import masalah_naskah, nilai_probe, unggah_diizinkan
from kpai.kunci import KunciSlot, SlotTerkunci
from kpai.ledger import boleh_ulang, cari, catat, kunci_berkas, simpan
from kpai.mode import boleh_berbayar, boleh_horde, platform_aktif
from kpai.render import Renderer
from kpai.template_naskah import template_lokal
from kpai.topik import mirip
from kpai.tts import Kata
from kpai.upload_youtube import kanal_sesuai, upload
from kpai.video import Adegan
from tests.test_fallback import jpeg_bytes


class Respon:
    def __init__(self, status=500, teks="server error"):
        self.status_code = status
        self.content = b""
        self.text = teks
        self.headers = {}

    def json(self):
        raise ValueError("bukan json")


class TestMode(unittest.TestCase):
    def test_mode_gratis_menutup_fal_dan_horde(self):
        with patch.object(config, "FREE_ONLY", True), patch.object(config, "PAID_FALLBACK_ENABLED", True), \
                patch.object(config, "PROVIDER_MODE", "auto_fallback"), patch.object(config, "HORDE_ENABLED", True), \
                patch.object(config, "IMAGE_FALLBACK_ENABLED", True):
            self.assertFalse(boleh_berbayar())
        with patch.object(config, "FREE_ONLY", True), patch.object(config, "PROVIDER_MODE", "free_safe"), \
                patch.object(config, "HORDE_ENABLED", True):
            self.assertFalse(boleh_horde())

    def test_youtube_only_tidak_mengizinkan_platform_lain(self):
        with patch.object(config, "PLATFORM_MODE", "youtube_only"), patch.object(config, "TELEGRAM_ENABLED", True):
            self.assertTrue(platform_aktif("youtube"))
            self.assertTrue(platform_aktif("telegram"))
            self.assertFalse(platform_aktif("tiktok"))

    def test_metadata_tidak_menulis_tiktok(self):
        naskah = template_lokal(("Fisika", "x"), ("Hewan", "y"), "besok")
        folder = Path(tempfile.mkdtemp())
        with patch.object(config, "PLATFORM_MODE", "youtube_only"):
            simpan_metadata(folder, naskah, "Fisika")
        self.assertTrue((folder / "youtube.txt").is_file())
        self.assertFalse((folder / "caption_tiktok.txt").exists())
        self.assertIn("bantuan AI", (folder / "youtube.txt").read_text(encoding="utf-8"))


class TestBatasDanTopik(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.riwayat = self.folder / "history.json"
        self.patch = patch.object(config, "HISTORY_FILE", self.riwayat)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_maksimal_lima_dan_slot_duplikat(self):
        data = history.muat()
        history.catat(data, {
            "tanggal": "2026-10-19", "slot": "pagi", "kategori": "Fisika",
            "topik": "topik pagi", "judul": "judul", "inti": "inti pagi", "status": "selesai",
        })
        history.simpan(data)
        lagi = history.muat()
        boleh, alasan = history.boleh_slot_baru(lagi, date(2026, 10, 19), "pagi")
        self.assertFalse(boleh)
        self.assertEqual(alasan, "slot sudah dibuat")
        with patch.object(config, "MAX_VIDEO_HARIAN", 1):
            boleh, alasan = history.boleh_slot_baru(lagi, date(2026, 10, 19), "siang")
            self.assertFalse(boleh)
            self.assertEqual(alasan, "batas harian")
        boleh, _alasan = history.boleh_slot_baru(lagi, date(2026, 10, 19), "siang")
        self.assertTrue(boleh)
        self.assertEqual(history.muat()["video"][0]["topik"], "topik pagi")

    def test_topik_mirip_dan_yang_berbeda(self):
        self.assertTrue(mirip("Matahari tiba-tiba menghilang", "Jika Matahari lenyap"))
        self.assertFalse(mirip("Matahari menghilang", "Bulan menghilang"))
        self.assertTrue(mirip("gravitasi dua kali lebih kuat", "gravitasi menjadi dua kali"))
        naskah = template_lokal(("Luar Angkasa", "x"), ("Fisika", "y"), "besok")
        from kpai.kualitas import masalah_duplikat
        self.assertTrue(masalah_duplikat(naskah, ["matahari hilang"]))
        self.assertFalse(masalah_duplikat(naskah, ["paus biru hilang"]))

    def test_kegagalan_satu_slot_tidak_menghentikan_berikutnya(self):
        def fungsi(slot):
            if slot == "siang":
                raise RuntimeError("kuota")
            return "selesai"

        hasil = jalankan_berurutan(["pagi", "siang", "sore"], fungsi)
        self.assertEqual([item["status"] for item in hasil], ["selesai", "gagal", "selesai"])
        self.assertIn("kuota", hasil[1]["alasan"])


class TestGambarLokal(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.patches = [
            patch.object(config, "CF_ACCOUNT_ID", "akun"),
            patch.object(config, "CF_API_TOKEN", "token"),
            patch.object(config, "CF_IMAGE_MODELS", ["model"]),
            patch.object(config, "CF_IMAGE_MODELS_HEMAT", ["model"]),
            patch.object(config, "IMAGE_STYLE", "cinematic"),
            patch.object(config, "PROVIDER_MODE", "free_safe"),
            patch.object(config, "FREE_ONLY", True),
            patch.object(config, "PAID_FALLBACK_ENABLED", True),
            patch.object(config, "IMAGE_FALLBACK_ENABLED", True),
            patch.object(config, "FAL_KEY", "fal-uji"),
            patch.object(config, "FAL_MODEL", "fal-ai/flux/schnell"),
            patch.object(config, "IMAGE_FALLBACK_MAX_COST_USD_PER_JOB", "5"),
            patch.object(config, "HORDE_ENABLED", True),
            patch.object(config, "IMAGE_LOCAL_FALLBACK", True),
            patch.object(config, "IMAGE_DAILY_MAX", 20),
            patch.object(config, "KUOTA_FILE", self.tmp / "kuota.json"),
            patch.object(config, "COOLDOWN_FILE", self.tmp / "cooldown.json"),
            patch.object(config, "CACHE_DIR", self.tmp / "cache"),
        ]
        for item in self.patches:
            item.start()
        self.addCleanup(lambda: [item.stop() for item in self.patches])

    def test_gratis_tidak_memanggil_fal_meski_saklar_nyala(self):
        url = []

        def pengirim(alamat, **_k):
            url.append(alamat)
            return Respon()

        folder = self.tmp / "out"
        folder.mkdir()
        aset = self.tmp / "aset"
        aset.mkdir()
        with self.assertRaises(NeedsReview):
            buat_gambar({"hook": "sun disappearing over earth"}, folder, 1, pengirim, pengirim, tidur=lambda _d: None, folder_aset=aset)
        self.assertFalse(any("fal.run" in item for item in url))
        self.assertFalse(any("aihorde.net" in item for item in url))

    def test_aset_lokal_yang_sesuai_dan_bukan_acak(self):
        aset = self.tmp / "aset"
        aset.mkdir()
        (aset / "acak.jpg").write_bytes(jpeg_bytes())
        for nama in ("hook", "awal", "puncak", "penutup"):
            (aset / f"{nama}.jpg").write_bytes(jpeg_bytes())

        def pengirim(alamat, **_k):
            return Respon(429, "daily free allocation exceeded")

        folder = self.tmp / "jadi"
        folder.mkdir()
        hasil = buat_gambar(
            {"hook": "a", "awal": "b", "puncak": "c", "penutup": "d"},
            folder, 1, pengirim, pengirim, tidur=lambda _d: None, folder_aset=aset,
        )
        self.assertTrue(all(item.provider == "Aset lokal" for item in hasil.catatan))
        self.assertTrue((folder / "gambar_hook.jpg").is_file())

    def test_batas_harian_tidak_memanggil_cloudflare(self):
        config.IMAGE_DAILY_MAX = 0
        url = []

        def pengirim(alamat, **_k):
            url.append(alamat)
            return Respon()

        folder = self.tmp / "habis"
        folder.mkdir()
        with self.assertRaises(NeedsReview):
            buat_gambar({"hook": "sun"}, folder, 1, pengirim, pengirim, tidur=lambda _d: None, folder_aset=folder / "kosong")
        self.assertEqual(url, [])


class TestUploadDanRender(unittest.TestCase):
    def test_uji_dan_dry_run_tidak_pernah_upload(self):
        self.assertFalse(unggah_diizinkan(
            uji=True, dry_run=False, yt_upload=True, kualitas_lolos=True, sudah_unggah=False, platform="youtube",
        ))
        self.assertFalse(unggah_diizinkan(
            uji=False, dry_run=True, yt_upload=True, kualitas_lolos=True, sudah_unggah=False, platform="youtube",
        ))
        self.assertFalse(unggah_diizinkan(
            uji=False, dry_run=False, yt_upload=True, kualitas_lolos=True, sudah_unggah=False, platform="tiktok",
        ))
        with patch.object(config, "MODE_UJI", True), patch.object(config, "YT_UPLOAD", True), \
                patch.object(config, "PLATFORM_MODE", "youtube_only"):
            with self.assertRaises(SystemExit):
                upload(Path("tidak-ada.mp4"), "judul", "deskripsi", ["shorts"])

    def test_ledger_mencegah_upload_kedua(self):
        folder = Path(tempfile.mkdtemp())
        video = folder / "a.mp4"
        video.write_bytes(b"video-palsu-untuk-hash")
        data = {"unggahan": []}
        kunci = kunci_berkas(video)
        self.assertTrue(boleh_ulang(None))
        catat(data, {"kunci": kunci, "id_video": "id-1", "status": "berhasil", "video_id": "abc"})
        self.assertFalse(boleh_ulang(cari(data, kunci)["status"]))
        catat(data, {"kunci": kunci, "id_video": "id-1", "status": "tidak_pasti", "video_id": ""})
        self.assertFalse(boleh_ulang("tidak_pasti"))
        with patch.object(config, "LEDGER_FILE", folder / "ledger.json"):
            simpan(data)
            self.assertEqual(cari({"unggahan": data["unggahan"]}, "id-1")["status"], "tidak_pasti")

    def test_kanal_harus_sesuai(self):
        self.assertTrue(kanal_sesuai("AI WHAT IF?", "ai what if?"))
        self.assertFalse(kanal_sesuai("KerjaPakaiAI", "AI WHAT IF?"))

    def test_probe_menolak_rasio_dan_durasi_salah(self):
        buruk = {
            "streams": [
                {"codec_type": "video", "codec_name": "h264", "width": 1920, "height": 1080},
                {"codec_type": "audio", "codec_name": "aac"},
            ],
            "format": {"duration": "12"},
        }
        masalah = nilai_probe(buruk)
        self.assertTrue(any("9:16" in item for item in masalah))
        self.assertTrue(any("durasi" in item for item in masalah))
        baik = {
            "streams": [
                {"codec_type": "video", "codec_name": "h264", "width": 1080, "height": 1920},
                {"codec_type": "audio", "codec_name": "aac"},
            ],
            "format": {"duration": "42"},
        }
        self.assertEqual(nilai_probe(baik), [])

    def test_frame_vertikal(self):
        naskah = template_lokal(("Fisika", "x"), ("Hewan", "y"), "besok")
        gambar = {adegan.id: Image.new("RGB", (480, 800), (20, 30, 50)) for adegan in naskah.adegan}
        adegan = []
        mulai = 0.0
        for scene in naskah.adegan:
            kata = [Kata(k, i * 0.3, (i + 1) * 0.3) for i, k in enumerate(scene.narasi.split()[:6])]
            item = Adegan(scene.id, Path("suara.mp3"), kata, 2.0, mulai=mulai)
            adegan.append(item)
            mulai += item.panjang
        renderer = Renderer(naskah, "Fisika", "AI WHAT IF?", gambar, 3, adegan, "nanti")
        frame = renderer.frame(0.4)
        self.assertEqual(frame.size, (1080, 1920))
        self.assertEqual(frame.mode, "RGB")

    def test_klaim_berlebihan_ditahan(self):
        naskah = template_lokal(("Fisika", "x"), ("Hewan", "y"), "besok")
        naskah.judul_youtube = "Kamu tidak akan percaya gravitasi"
        self.assertTrue(any("klaim" in item for item in masalah_naskah(naskah)))

    def test_mode_lokal_tidak_memanggil_edge(self):
        from kpai.tts import buat_suara
        folder = Path(tempfile.mkdtemp())
        with patch.object(config, "PROVIDER_MODE", "local_only"), \
                patch.object(config, "TTS_PROVIDER", "edge_tts"), \
                patch("edge_tts.Communicate", side_effect=AssertionError("edge tidak boleh dipanggil")):
            with self.assertRaises(NeedsReview):
                buat_suara("Ini kalimat cadangan yang tidak boleh dikirim ke layanan suara.", folder / "suara_hook.mp3", nama="hook")

    def test_kunci_slot_menolak_proses_kedua(self):
        folder = Path(tempfile.mkdtemp())
        with patch.object(config, "LOCK_DIR", folder), patch.object(config, "LOCK_DETIK", 3000):
            with KunciSlot("2026-10-19-pagi"):
                with self.assertRaises(SlotTerkunci):
                    with KunciSlot("2026-10-19-pagi"):
                        pass


if __name__ == "__main__":
    unittest.main()
