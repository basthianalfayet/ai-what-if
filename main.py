import argparse
import json
import os
import shutil
import sys
import traceback
import uuid
from datetime import date
from pathlib import Path

from kpai import config, history, telegram
from kpai.caption import caption_menarik, deskripsi_youtube, judul_youtube, simpan_metadata, tag_youtube
from kpai.errors import NeedsReview, redaksi
from kpai.images import buat_gambar
from kpai.jalan import jalankan_berurutan
from kpai.kualitas import masalah_duplikat, masalah_naskah, periksa_berkas, unggah_diizinkan
from kpai.kunci import KunciSlot, SlotTerkunci
from kpai.laporan import laporan_needs_review, laporan_selesai, laporan_video
from kpai.mode import mode
from kpai.render import Renderer
from kpai.script_gen import HasilNaskah, Naskah, buat_naskah, jumlah_kata_narasi, rapikan
from kpai.video import buat_suara_adegan, render_video


def _args():
    p = argparse.ArgumentParser(description="Bikin video Shorts AI WHAT IF?")
    p.add_argument("--slot", choices=["pagi", "siang", "sore", "malam", "larut", "auto"], default="auto")
    p.add_argument("--tanggal", help="YYYY-MM-DD, default hari ini (WIB)")
    p.add_argument("--topik", help="Paksa topik tertentu")
    p.add_argument("--naskah", help="Pakai naskah JSON sendiri, tanpa memanggil model")
    p.add_argument("--uji", action="store_true", help="Mode uji: tidak upload, tidak dicatat di riwayat")
    p.add_argument("--dry-run", action="store_true", help="Tidak pernah upload dan tidak mencatat riwayat")
    p.add_argument("--paksa", action="store_true", help="Tetap buat walau video slot ini sudah ada")
    p.add_argument("--batch", action="store_true", help="Buat sampai lima slot yang belum ada hari ini")
    p.add_argument("--login", action="store_true", help="Login YouTube kanal AI WHAT IF? lalu keluar")
    p.add_argument("--telegram-id", action="store_true", help="Tampilkan chat ID Telegram lalu keluar")
    p.add_argument("--cek", action="store_true", help="Tampilkan konfigurasi tanpa memanggil API")
    return p.parse_args()


def _tautan_run() -> str:
    repo = os.getenv("GITHUB_REPOSITORY", "")
    run_id = os.getenv("GITHUB_RUN_ID", "")
    if repo and run_id:
        return f"https://github.com/{repo}/actions/runs/{run_id}"
    return ""


def _kabari(teks: str) -> None:
    try:
        telegram.kirim_pesan(redaksi(teks))
    except RuntimeError as e:
        print(f"  Telegram gagal: {e}")


def _kirim_hasil(video, caption_video: str, pesan: str, peringatan: list[str]) -> None:
    if not telegram.aktif():
        print("  Telegram belum diisi atau dimatikan. Video hanya tersimpan di folder output.")
        return
    try:
        telegram.kirim_video(video, redaksi(caption_video)[:1024], 0)
        print("  Video terkirim ke Telegram")
    except RuntimeError as e:
        print(f"  Video gagal terkirim: {e}")
        peringatan.append(f"Video gagal terkirim ke Telegram: {e}")
    if peringatan:
        pesan += "\n\nPeringatan:\n" + "\n".join(f"- {redaksi(p)}" for p in peringatan)
    tautan = _tautan_run()
    if tautan:
        pesan += f"\n\n{tautan}"
    _kabari(pesan)


def _tulis_log(folder: Path | None, catatan: dict) -> None:
    teks = laporan_video(catatan)
    print(teks)
    if folder is not None:
        (folder / "laporan.json").write_text(json.dumps(catatan, ensure_ascii=False, indent=2), encoding="utf-8")
        (folder / "laporan.txt").write_text(teks + "\n", encoding="utf-8")


def _cek() -> None:
    from kpai.mode import boleh_berbayar, boleh_horde, sisa_gambar

    print(f"Kanal: {config.CHANNEL_NAME}")
    print(f"Platform: {config.PLATFORM_MODE}")
    print(f"Mode provider: {mode()}")
    print(f"FREE_ONLY: {config.FREE_ONLY}")
    print(f"Fallback berbayar: {'diizinkan' if boleh_berbayar() else 'diblokir'}")
    print(f"AI Horde: {'aktif' if boleh_horde() else 'mati'}")
    print(f"Gemini: {'terisi' if config.GEMINI_API_KEY else 'kosong'}")
    print(f"Groq: {'terisi' if config.GROQ_API_KEY else 'kosong'}")
    print(f"Cloudflare: {'terisi' if config.CF_ACCOUNT_ID and config.CF_API_TOKEN else 'kosong'}")
    print(f"Sisa gambar hari ini: {sisa_gambar()} dari {config.IMAGE_DAILY_MAX}")
    print(f"YouTube upload: {'nyala' if config.YT_UPLOAD else 'mati'} ({config.YT_PRIVACY})")
    print(f"Nama kanal yang dicek: {config.YT_CHANNEL_NAME}")
    print(f"Token baru: {'ada' if (config.YT_DIR / 'token.json').exists() else 'belum ada'}")
    if (config.SECRETS_DIR / "token.json").exists():
        print("Token lama secrets/token.json ada dan tidak akan dipakai.")
    print(f"Riwayat: {config.HISTORY_FILE}")
    print(f"Telegram: {'aktif' if telegram.aktif() else 'mati'}")
    print(f"Adegan per video: {config.IMAGE_PER_VIDEO}")
    if config.IMAGE_PER_VIDEO != 4:
        print("Versi ini merender 4 adegan. IMAGE_PER_VIDEO selain 4 belum didukung.")


def _muat_naskah(path: str, kategori_default: str) -> HasilNaskah:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if "prompt" in data and "adegan" not in data:
        raise NeedsReview("Naskah lama KerjaPakaiAI tidak dipakai di kanal ini. Lihat contoh_naskah.json.")
    if not data.get("kategori"):
        data["kategori"] = kategori_default
    return HasilNaskah(rapikan(Naskah.model_validate(data)), "File JSON", "json")


def _salin_aset(asal: Path, folder: Path) -> None:
    if not asal.is_dir():
        return
    for pola in ("gambar_*.jpg", "gambar_*.jpeg", "gambar_*.png", "suara_*.mp3"):
        for berkas in asal.glob(pola):
            shutil.copy2(berkas, folder / berkas.name)


def buat_video(a, tgl: date, slot: str) -> str:
    run_id = uuid.uuid4().hex[:8]
    if os.getenv("GITHUB_RUN_ID"):
        run_id = f"{os.environ['GITHUB_RUN_ID'][-6:]}-{run_id}"
    tanpa_catat = bool(a.uji or a.dry_run)
    tgl_berikut, slot_berikut = config.slot_berikut(tgl, slot)
    kategori = config.kategori_untuk(tgl, slot)
    kategori_berikut = config.kategori_untuk(tgl_berikut, slot_berikut)
    label_berikut = config.label_berikut(slot)
    riwayat = history.muat()
    catatan = {
        "run_id": run_id,
        "slot": slot,
        "waktu": f"{tgl.isoformat()} {config.JADWAL_WIB[slot]} WIB",
        "topik": "",
        "status": "",
        "naskah": {},
        "retry": 0,
        "gambar": "",
        "suara": "",
        "render": "",
        "kualitas": {"lolos": False, "masalah": []},
        "upload": {"status": "tidak dijalankan", "video_id": ""},
        "folder": "",
        "alasan": "",
        "peringatan": [],
    }

    if not tanpa_catat and not a.paksa:
        boleh, alasan = history.boleh_slot_baru(riwayat, tgl, slot, paksa=False)
        if not boleh:
            pesan = f"Video {tgl} {slot} dilewati: {alasan}."
            print(pesan)
            catatan["status"] = "dilewati"
            catatan["alasan"] = alasan
            _kabari(pesan)
            return "dilewati"

    nama_kunci = f"{tgl}-{slot}" if not tanpa_catat else f"{tgl}-{slot}-uji-{run_id}"
    try:
        with KunciSlot(nama_kunci):
            if not tanpa_catat and not a.paksa:
                riwayat = history.muat()
                boleh, alasan = history.boleh_slot_baru(riwayat, tgl, slot, paksa=False)
                if not boleh:
                    print(f"Video {tgl} {slot} dilewati: {alasan}.")
                    return "dilewati"
            return _produksi(a, tgl, slot, run_id, tanpa_catat, kategori, kategori_berikut, label_berikut, tgl_berikut, slot_berikut, riwayat, catatan)
    except SlotTerkunci as e:
        print(redaksi(str(e)))
        _kabari(f"Slot {tgl} {slot} sedang berjalan di proses lain. Proses ini berhenti.")
        return "gagal"


def _produksi(a, tgl, slot, run_id, tanpa_catat, kategori, kategori_berikut, label_berikut, tgl_berikut, slot_berikut, riwayat, catatan) -> str:
    peringatan = catatan["peringatan"]
    folder = config.OUTPUT_DIR / f"{'uji-' if tanpa_catat else ''}{tgl}-{slot}-{run_id}"
    folder.mkdir(parents=True, exist_ok=True)
    catatan["folder"] = str(folder)

    if mode() == "local_only" and not a.naskah:
        catatan["status"] = "review"
        catatan["alasan"] = "Mode lokal butuh --naskah beserta gambar dan audio yang sudah tersimpan."
        _tulis_log(folder, catatan)
        _kabari(f"NEEDS_REVIEW {tgl} {slot}: {catatan['alasan']}")
        _catat(riwayat, tanpa_catat, tgl, slot, kategori[0], catatan, None, None)
        return "review"

    if a.naskah:
        hasil_teks = _muat_naskah(a.naskah, kategori[0])
        _salin_aset(Path(a.naskah).parent, folder)
        print(f"[1/5] Naskah dari {a.naskah}")
    else:
        print(f"[1/5] Naskah ({config.HARI[tgl.weekday()]} {slot}, {kategori[0]})")
        hasil_teks = buat_naskah(
            kategori, kategori_berikut, label_berikut,
            topik=a.topik or riwayat["rencana"].get(history.kunci(tgl, slot)),
            hindari=history.topik_lama(riwayat),
        )
        for pesan in hasil_teks.konfigurasi:
            print(f"  {pesan}")
            _kabari(pesan)
        if hasil_teks.peringatan:
            peringatan.append(hasil_teks.peringatan)
    naskah = hasil_teks.naskah
    naskah.id_video = f"{tgl.isoformat()}-{slot}-{run_id}"
    if not naskah.kategori:
        naskah.kategori = kategori[0]
    catatan["topik"] = naskah.topik
    catatan["retry"] = hasil_teks.percobaan
    catatan["naskah"] = {
        "provider": hasil_teks.provider,
        "model": hasil_teks.model,
        "fallback": hasil_teks.fallback_dari or "",
        "alasan": hasil_teks.alasan or "",
    }
    print(f"  Provider teks: {hasil_teks.provider}")
    print(f"  Topik: {naskah.topik}")
    print(f"  Judul: {naskah.judul_kerja}  ({jumlah_kata_narasi(naskah)} kata narasi)")
    (folder / "naskah.json").write_text(
        json.dumps(naskah.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8"
    )

    if hasil_teks.ditolak:
        catatan["status"] = "review"
        catatan["alasan"] = hasil_teks.peringatan or "Topik terlalu mirip dengan riwayat."
        _tulis_log(folder, catatan)
        _kabari(f"NEEDS_REVIEW {tgl} {slot}: {catatan['alasan']}")
        _catat(riwayat, tanpa_catat, tgl, slot, naskah.kategori, catatan, naskah, None)
        return "review"

    print("[2/5] Gambar")
    try:
        hasil_gambar = buat_gambar(
            {adegan.id: adegan.prompt_gambar for adegan in naskah.adegan},
            folder,
            seed=tgl.toordinal(),
        )
    except NeedsReview as e:
        for pesan in e.konfigurasi:
            _kabari(pesan)
        alasan = redaksi(str(e))
        teks = laporan_needs_review(hasil_teks, alasan, peringatan + e.peringatan)
        catatan["status"] = "review"
        catatan["alasan"] = alasan
        catatan["gambar"] = alasan
        _tulis_log(folder, catatan)
        print(teks)
        _kabari(teks)
        _catat(riwayat, tanpa_catat, tgl, slot, naskah.kategori, catatan, naskah, None)
        return "review"
    for pesan in hasil_gambar.konfigurasi:
        _kabari(pesan)
    peringatan.extend(hasil_gambar.peringatan)
    catatan["gambar"] = ", ".join(f"{item.scene}:{item.provider}" for item in hasil_gambar.catatan) or "tidak ada"

    print("[3/5] Suara")
    try:
        adegan = buat_suara_adegan(naskah, folder)
    except NeedsReview as e:
        catatan["status"] = "review"
        catatan["alasan"] = redaksi(str(e))
        catatan["suara"] = catatan["alasan"]
        _tulis_log(folder, catatan)
        _kabari(f"NEEDS_REVIEW {tgl} {slot}: {catatan['alasan']}")
        _catat(riwayat, tanpa_catat, tgl, slot, naskah.kategori, catatan, naskah, None)
        return "review"
    catatan["suara"] = "siap"

    print("[4/5] Render")
    try:
        indeks_tema = tgl.toordinal() * len(config.SLOT) + config.SLOT.index(slot)
        renderer = Renderer(naskah, naskah.kategori, config.CHANNEL_NAME, hasil_gambar.gambar, indeks_tema, adegan, label_berikut)
        video = folder / f"AI-WHAT-IF-{tgl}-{slot}.mp4"
        total = render_video(renderer, adegan, folder, video)
        catatan["render"] = f"siap {total:.1f} detik"
        print(f"  Video jadi: {video}  ({total:.1f} detik)")
    except Exception as e:
        catatan["status"] = "review"
        catatan["render"] = "gagal"
        catatan["alasan"] = redaksi(str(e))
        _tulis_log(folder, catatan)
        _kabari(f"NEEDS_REVIEW {tgl} {slot}: render gagal: {catatan['alasan']}")
        _catat(riwayat, tanpa_catat, tgl, slot, naskah.kategori, catatan, naskah, None)
        return "review"

    judul = judul_youtube(naskah, naskah.kategori)
    deskripsi = deskripsi_youtube(naskah, naskah.kategori)
    caption = caption_menarik(naskah, naskah.kategori)
    simpan_metadata(folder, naskah, naskah.kategori)

    masalah = masalah_naskah(naskah) + periksa_berkas(video)
    if not a.topik and not a.paksa:
        masalah += masalah_duplikat(naskah, history.topik_lama(riwayat))
    catatan["kualitas"] = {"lolos": not masalah, "masalah": masalah}

    youtube_id = None
    if unggah_diizinkan(
        uji=bool(a.uji),
        dry_run=bool(a.dry_run),
        yt_upload=config.YT_UPLOAD,
        kualitas_lolos=not masalah,
        sudah_unggah=False,
        platform="youtube",
    ):
        print(f"[5/5] Upload YouTube ({config.YT_PRIVACY})")
        from kpai.upload_youtube import upload
        try:
            youtube_id = upload(video, judul, deskripsi, tag_youtube(naskah, naskah.kategori), naskah.id_video)
            catatan["upload"] = {"status": "berhasil", "video_id": youtube_id}
            print(f"  https://youtube.com/shorts/{youtube_id}")
        except SystemExit as e:
            peringatan.append(f"Upload YouTube dilewati: {e}")
            catatan["upload"] = {"status": "dilewati", "video_id": ""}
            print(f"  Upload dilewati: {e}")
        except Exception as e:
            peringatan.append(f"Upload YouTube gagal: {redaksi(e)}")
            catatan["upload"] = {"status": "gagal", "video_id": ""}
            print(f"  Upload gagal, video tetap tersimpan: {redaksi(e)}")
    else:
        alasan_unggah = "pemeriksaan kualitas" if masalah else "upload mati atau mode uji"
        print(f"[5/5] Upload tidak dijalankan ({alasan_unggah})")
        catatan["upload"] = {"status": "tidak dijalankan", "video_id": ""}

    if masalah:
        catatan["status"] = "review"
        catatan["alasan"] = "; ".join(masalah)
        laporan = "NEEDS_REVIEW\n" + laporan_video(catatan)
    else:
        catatan["status"] = "terunggah" if youtube_id else "selesai"
        laporan = laporan_selesai(hasil_teks, hasil_gambar.catatan) + "\n" + laporan_video(catatan)
    _tulis_log(folder, catatan)
    _kirim_hasil(video, caption, laporan, peringatan)
    _catat(riwayat, tanpa_catat, tgl, slot, naskah.kategori, catatan, naskah, youtube_id, tgl_berikut, slot_berikut)
    print("Selesai." if not masalah else "Selesai dengan status NEEDS_REVIEW.")
    return "review" if masalah else "selesai"


def _catat(riwayat, tanpa_catat, tgl, slot, kategori, catatan, naskah, youtube_id, tgl_berikut=None, slot_berikut=None) -> None:
    if tanpa_catat or catatan["status"] not in ("selesai", "review", "terunggah"):
        return
    history.catat(riwayat, {
        "tanggal": tgl.isoformat(),
        "slot": slot,
        "kategori": kategori,
        "topik": catatan.get("topik") or "",
        "judul": getattr(naskah, "judul_kerja", "") if naskah else "",
        "inti": getattr(naskah, "inti", "") if naskah else "",
        "youtube_id": youtube_id,
        "status": catatan["status"],
        "run_id": catatan["run_id"],
        "folder": catatan.get("folder") or "",
    })
    if naskah is not None and tgl_berikut and slot_berikut and getattr(naskah, "topik_berikut", ""):
        riwayat["rencana"][history.kunci(tgl_berikut, slot_berikut)] = naskah.topik_berikut
    history.simpan(riwayat)


def _jalankan(a, tgl: date, slot: str) -> str:
    try:
        return buat_video(a, tgl, slot)
    except NeedsReview as e:
        pesan = f"NEEDS_REVIEW {tgl} {slot}: {redaksi(e)}"
        print(pesan)
        _kabari(pesan)
        return "review"
    except Exception as e:
        traceback.print_exc()
        tautan = _tautan_run()
        ekor = f"\n{tautan}" if tautan else ""
        _kabari(f"GAGAL bikin video {tgl} {slot}:\n{type(e).__name__}: {redaksi(e)}{ekor}")
        return "gagal"


def main():
    a = _args()
    config.MODE_UJI = bool(a.uji or a.dry_run)
    config.DRY_RUN = bool(a.dry_run)
    if a.login:
        from kpai.upload_youtube import login
        kredensial = login(interaktif=True)
        from kpai.upload_youtube import _judul_kanal
        judul = _judul_kanal(kredensial)
        print(f"Login YouTube berhasil untuk kanal: {judul}")
        print("Token disimpan di secrets/youtube_whatif/token.json")
        if judul.casefold().strip() != config.YT_CHANNEL_NAME.casefold().strip():
            print(f"Peringatan: nama kanal bukan '{config.YT_CHANNEL_NAME}'. Set YT_CHANNEL_NAME kalau memang ini kanal yang benar.")
        return
    if a.telegram_id:
        telegram.cari_chat_id()
        return
    if a.cek:
        _cek()
        return

    sekarang = config.sekarang_wib()
    tgl = date.fromisoformat(a.tanggal) if a.tanggal else sekarang.date()
    if a.batch:
        hasil = jalankan_berurutan(config.SLOT, lambda slot: _jalankan(a, tgl, slot))
        status = [item["status"] for item in hasil]
        print("Batch:", ", ".join(f"{item['item']}={item['status']}" for item in hasil))
        if any(item == "gagal" for item in status):
            sys.exit(1)
        if any(item == "review" for item in status):
            sys.exit(2)
        return

    slot = a.slot if a.slot != "auto" else config.slot_otomatis(sekarang.hour)
    status = _jalankan(a, tgl, slot)
    if status == "gagal":
        sys.exit(1)
    if status == "review":
        sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
