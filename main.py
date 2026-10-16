import argparse
import json
import os
import shutil
import sys
import traceback
from datetime import date

from kpai import config, history, telegram
from kpai.caption import caption_menarik, deskripsi_youtube, judul_youtube, tag_youtube
from kpai.errors import NeedsReview
from kpai.images import buat_gambar
from kpai.laporan import laporan_needs_review, laporan_selesai
from kpai.render import Renderer
from kpai.script_gen import HasilNaskah, Naskah, buat_naskah, jumlah_kata_narasi, rapikan
from kpai.video import buat_suara_adegan, render_video


def _args():
    p = argparse.ArgumentParser(description="Bikin 1 video Shorts/TikTok KerjaPakaiAI.")
    p.add_argument("--slot", choices=["pagi", "siang", "sore", "malam", "larut", "auto"], default="auto",
                   help="Slot video. auto mengikuti jam WIB: pagi <10, siang <14, sore <18, malam <20, selain itu larut")
    p.add_argument("--tanggal", help="YYYY-MM-DD, default hari ini (WIB)")
    p.add_argument("--topik", help="Paksa topik tertentu, selain itu ide dipilih Gemini")
    p.add_argument("--naskah", help="Pakai naskah JSON sendiri, tanpa Gemini")
    p.add_argument("--uji", action="store_true", help="Mode uji: tidak upload, tidak dicatat di riwayat")
    p.add_argument("--paksa", action="store_true", help="Tetap buat walau video slot ini sudah ada")
    p.add_argument("--login", action="store_true", help="Login YouTube sekali lalu keluar")
    p.add_argument("--telegram-id", action="store_true", help="Tampilkan chat ID Telegram lalu keluar")
    return p.parse_args()


def _pesan_siap_tempel(n: Naskah, kategori: str) -> str:
    return (
        "CAPTION TIKTOK (siap tempel)\n"
        f"{caption_menarik(n, kategori)}\n\n"
        "YOUTUBE — judul\n"
        f"{judul_youtube(n, kategori)}\n\n"
        "YOUTUBE — deskripsi\n"
        f"{deskripsi_youtube(n, kategori)}"
    )


def _tautan_run() -> str:
    repo = os.getenv("GITHUB_REPOSITORY", "")
    run_id = os.getenv("GITHUB_RUN_ID", "")
    if repo and run_id:
        return f"https://github.com/{repo}/actions/runs/{run_id}"
    return ""


def _kabari(teks: str) -> None:
    try:
        telegram.kirim_pesan(teks)
    except RuntimeError as e:
        print(f"  Telegram gagal: {e}")


def _kirim_hasil(video, caption_video: str, pesan_caption: str, laporan: str, peringatan: list[str], total: float) -> None:
    if not telegram.aktif():
        print("  Telegram belum diisi, video hanya tersimpan di folder output")
        print(laporan)
        return
    try:
        telegram.kirim_video(video, caption_video[:1024], total)
        print("  Video terkirim ke Telegram")
    except RuntimeError as e:
        print(f"  Video gagal terkirim: {e}")
        peringatan.append(f"Video gagal terkirim ke Telegram: {e}. File tetap ada: {video}")
    _kabari(pesan_caption)
    if peringatan:
        laporan += "\n\nPeringatan:\n" + "\n".join(f"- {p}" for p in peringatan)
    tautan = _tautan_run()
    if tautan:
        laporan += f"\n\n{tautan}"
    _kabari(laporan)
    print("  Caption dan laporan terkirim ke Telegram")


def buat_video(a, tgl: date, slot: str):
    tgl_berikut, slot_berikut = config.slot_berikut(tgl, slot)
    kategori = config.kategori_untuk(tgl, slot)
    kategori_berikut = config.kategori_untuk(tgl_berikut, slot_berikut)
    label_berikut = config.label_berikut(slot)
    riwayat = history.muat()
    peringatan = []

    if not a.uji and not a.paksa and history.sudah_dibuat(riwayat, tgl, slot):
        pesan = f"Video {tgl} {slot} sudah dibuat, dilewati. Pakai --paksa kalau mau bikin ulang."
        print(pesan)
        _kabari(pesan)
        return

    if a.naskah:
        with open(a.naskah, encoding="utf-8") as f:
            data = json.load(f)
        kategori = (data.get("kategori", kategori[0]), "")
        print(f"[1/5] Naskah dari {a.naskah} ({kategori[0]})")
        hasil_teks = HasilNaskah(rapikan(Naskah.model_validate(data)), "File JSON", "json")
    else:
        print(f"[1/5] Naskah ({config.HARI[tgl.weekday()]} {slot}, {kategori[0]})")
        topik = a.topik or riwayat["rencana"].get(history.kunci(tgl, slot))
        if topik and not a.topik:
            print(f"  Ide dari video sebelumnya: {topik}")
        else:
            print("  Ide dipilih AI")
        hasil_teks = buat_naskah(
            kategori, kategori_berikut, label_berikut,
            topik=topik,
            hindari=history.topik_lama(riwayat),
            rekap_minggu=history.minggu_ini(riwayat, tgl) if tgl.weekday() == 6 and slot == "pagi" else (),
        )
        for pesan in hasil_teks.konfigurasi:
            print(f"  {pesan}")
            _kabari(pesan)
        if hasil_teks.peringatan:
            peringatan.append(hasil_teks.peringatan)
    naskah = hasil_teks.naskah
    print(f"  Provider teks: {hasil_teks.provider}")
    print(f"  Topik: {naskah.topik}")
    print(f"  Judul: {naskah.judul}  ({jumlah_kata_narasi(naskah)} kata narasi)")

    nama_folder = f"{'uji-' if a.uji else ''}{tgl}-{slot}"
    folder = config.OUTPUT_DIR / nama_folder
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    (folder / "naskah.json").write_text(
        json.dumps({"kategori": kategori[0], **naskah.model_dump()}, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    indeks_tema = tgl.toordinal() * len(config.SLOT) + config.SLOT.index(slot)
    print("[2/5] Gambar AI")
    try:
        hasil_gambar = buat_gambar(
            {"hook": naskah.gambar_hook, "kerja": naskah.gambar_kerja,
             "trik": naskah.gambar_trik, "penutup": naskah.gambar_penutup},
            folder, seed=indeks_tema * 10,
        )
    except NeedsReview as e:
        for pesan in e.konfigurasi:
            _kabari(pesan)
        teks = laporan_needs_review(hasil_teks, str(e), peringatan + e.peringatan)
        tautan = _tautan_run()
        if tautan:
            teks += f"\n\n{tautan}"
        print(teks)
        _kabari(teks)
        raise SystemExit(1) from None
    for pesan in hasil_gambar.konfigurasi:
        _kabari(pesan)
    peringatan.extend(hasil_gambar.peringatan)
    gambar = hasil_gambar.gambar

    print("[3/5] Suara")
    adegan = buat_suara_adegan(naskah, folder)

    print("[4/5] Animasi & video")
    renderer = Renderer(naskah, kategori[0], config.CHANNEL_NAME, gambar, indeks_tema, adegan, label_berikut)
    video = folder / f"{config.CHANNEL_NAME}-{tgl}-{slot}.mp4"
    total = render_video(renderer, adegan, folder, video)
    for p in folder.glob("suara_*.mp3"):
        p.unlink()
    print(f"  Video jadi: {video}  ({total:.1f} detik)")

    judul_yt = judul_youtube(naskah, kategori[0])
    deskripsi = deskripsi_youtube(naskah, kategori[0])
    caption = caption_menarik(naskah, kategori[0])
    (folder / "youtube.txt").write_text(f"{judul_yt}\n\n{deskripsi}\n", encoding="utf-8")
    (folder / "caption_tiktok.txt").write_text(caption + "\n", encoding="utf-8")

    youtube_id = None
    if config.YT_UPLOAD and not a.uji:
        print(f"[5/5] Upload YouTube ({config.YT_PRIVACY})")
        from kpai.upload_youtube import upload
        try:
            youtube_id = upload(video, judul_yt, deskripsi, tag_youtube(naskah, kategori[0]))
            print(f"  https://youtube.com/shorts/{youtube_id}")
        except SystemExit as e:
            peringatan.append(f"Upload YouTube dilewati: {e}")
            print(f"  Upload dilewati: {e}")
        except Exception as e:
            peringatan.append(f"Upload YouTube gagal: {e}")
            print(f"  Upload gagal, video tetap tersimpan: {e}")
    else:
        print("[5/5] YouTube tidak diupload (upload manual dari Telegram)")

    pesan = _pesan_siap_tempel(naskah, kategori[0])
    if youtube_id:
        pesan += f"\n\nYouTube ({config.YT_PRIVACY}): https://studio.youtube.com/video/{youtube_id}/edit"
    laporan = laporan_selesai(hasil_teks, hasil_gambar.catatan)
    _kirim_hasil(video, caption, pesan, laporan, peringatan, total)

    if not a.uji:
        history.catat(riwayat, {
            "tanggal": tgl.isoformat(),
            "slot": slot,
            "kategori": kategori[0],
            "topik": naskah.topik,
            "judul": naskah.judul,
            "youtube_id": youtube_id,
        })
        riwayat["rencana"][history.kunci(tgl_berikut, slot_berikut)] = naskah.topik_besok
        history.simpan(riwayat)
    print("Selesai.")


def main():
    a = _args()
    if a.login:
        from kpai.upload_youtube import login
        login(interaktif=True)
        print("Login YouTube berhasil. Token disimpan di secrets/token.json")
        return
    if a.telegram_id:
        telegram.cari_chat_id()
        return

    sekarang = config.sekarang_wib()
    tgl = date.fromisoformat(a.tanggal) if a.tanggal else sekarang.date()
    slot = a.slot if a.slot != "auto" else config.slot_otomatis(sekarang.hour)
    try:
        buat_video(a, tgl, slot)
    except Exception as e:
        traceback.print_exc()
        tautan = _tautan_run()
        ekor = f"\n{tautan}" if tautan else ""
        _kabari(f"GAGAL bikin video {tgl} {slot}:\n{type(e).__name__}: {str(e)[:800]}{ekor}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
