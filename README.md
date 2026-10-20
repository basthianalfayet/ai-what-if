# AI WHAT IF? — YouTube Shorts

Kanal ini membuat video pendek vertikal berbahasa Indonesia tentang skenario hipotetis: luar angkasa, bumi, tubuh, hewan, fisika, teknologi, dan masa depan. Setiap video memisahkan hal yang cukup kita ketahui dari bagian yang hanya spekulasi. Ini fiksi, bukan berita.

Project ini memakai jalur produksi yang sudah ada (naskah, gambar, suara, FFmpeg, Telegram, YouTube, jadwal), lalu diarahkan ke kanal baru. Riwayat dan token YouTube kanal lama tidak dipakai.

Target: paling banyak **5 video per hari**, jam **07:00, 12:00, 16:00, 19:00, dan 21:00 WIB**. Durasi sasaran 35–55 detik, 1080×1920, H.264 + AAC.

## Arsitektur

```text
cron-job.org / laptop
        |
        v
GitHub Actions atau main.py
        |
        +-- kunci slot (data/locks, plus concurrency Actions)
        +-- riwayat topik (data/history_whatif.json)
        +-- naskah: Gemini -> Groq -> template lokal
        +-- gambar: Cloudflare -> cache / aset lokal
        |            (Horde dan fal.ai hanya jika dinyalakan eksplisit)
        +-- suara: Edge TTS -> audio lokal
        +-- render FFmpeg 9:16
        +-- pemeriksaan kualitas
        +-- YouTube hanya jika YT_UPLOAD=1, lolos cek, dan kanalnya cocok
        +-- Telegram sebagai notifikasi, bukan tempat publikasi kedua
```

File penting:

| Bagian | File |
|---|---|
| Perintah | `main.py` |
| Konfigurasi | `kpai/config.py`, `.env` |
| Mode provider | `kpai/mode.py` |
| Naskah | `kpai/script_gen.py`, `kpai/template_naskah.py` |
| Gambar dan cache | `kpai/images.py`, `cache/gambar/` |
| Suara dan render | `kpai/tts.py`, `kpai/render.py`, `kpai/video.py` |
| Kualitas | `kpai/kualitas.py` |
| Riwayat, kunci, upload | `kpai/history.py`, `kpai/kunci.py`, `kpai/ledger.py` |
| YouTube | `kpai/upload_youtube.py` |
| Jadwal | `.github/workflows/video.yml`, `pasang_jadwal.ps1` |

`data/history.json` adalah riwayat kanal lama dan tidak dibaca. Kanal ini memakai `data/history_whatif.json`.

## Alur satu video

1. Cek riwayat dan kunci. Slot yang sudah selesai, atau hari yang sudah 5 video, dilewati.
2. Pilih kategori dari hari dan slot, lalu tulis naskah JSON (4 adegan: hook, awal, puncak, penutup).
3. Buat atau pakai ulang 4 gambar.
4. Buat suara Indonesia dan subtitle dari timing audio yang sebenarnya.
5. Render MP4. Aset perantara (`naskah.json`, `gambar_*.jpg`, `suara_*.mp3`) tetap disimpan.
6. Periksa naskah, file, durasi, rasio, dan kemiripan topik.
7. Upload hanya jika semua syarat di bagian YouTube terpenuhi. Kalau tidak, statusnya `NEEDS_REVIEW`, bukan sukses diam-diam.

Satu slot yang gagal tidak membatalkan slot lain saat `--batch`.

## Kategori harian

Lima slot menggeser kategori supaya satu hari tidak bentrok. Contoh Senin:

| 07:00 pagi | 12:00 siang | 16:00 sore | 19:00 malam | 21:00 larut |
|---|---|---|---|---|
| Luar Angkasa | Bumi dan Alam | Tubuh Manusia | Hewan | Fisika |

Selasa bergeser satu langkah, dan seterusnya. Teknologi dan AI serta Masa Depan Peradaban masuk di hari berikutnya.

## Environment

Salin `.env.example` menjadi `.env`. Jangan commit `.env`, `secrets/`, atau token.

| Variabel | Default | Fungsi |
|---|---|---|
| `PLATFORM_MODE` | `youtube_only` | Hanya YouTube yang boleh menerima upload. TikTok tidak ditulis. |
| `PROVIDER_MODE` | `auto_fallback` | Cloudflare dulu. Kalau neuron habis, gambar pindah ke AI Horde. fal.ai tetap mati |
| `FREE_ONLY` | `true` | Menutup setiap panggilan berbayar |
| `PAID_FALLBACK_ENABLED` | `false` | Izin eksplisit untuk fal.ai |
| `SCRIPT_PROVIDER` | `gemini` | Provider naskah utama |
| `SCRIPT_FALLBACK_PROVIDER` | `groq` | Cadangan naskah |
| `SCRIPT_LOCAL_FALLBACK` | `true` | Template lokal jika API naskah habis |
| `IMAGE_PROVIDER` | `cloudflare` | Provider gambar |
| `IMAGE_LOCAL_FALLBACK` | `true` | Aset di `assets/fallback/{adegan}.jpg` |
| `IMAGE_PER_VIDEO` | `4` | Versi ini merender 4 adegan |
| `IMAGE_DAILY_MAX` | `20` | Batas permintaan gambar API per hari WIB |
| `HORDE_ENABLED` | `true` | Cadangan gambar gratis saat Cloudflare menolak. Antreannya bisa beberapa menit |
| `IMAGE_FALLBACK_ENABLED` | `false` | Saklar fal.ai. Tidak cukup sendirian |
| `TTS_PROVIDER` | `edge_tts` | Suara |
| `TTS_VOICE` / `TTS_RATE` | `id-ID-ArdiNeural` / `+5%` | Suara dan kecepatan |
| `MAX_VIDEO_HARIAN` | `5` | Batas video tercatat per hari |
| `MAX_RETRY` | `2` | Percobaan untuk kesalahan sementara |
| `YT_UPLOAD` | `1` | `0` mematikan upload. Mode uji tetap tidak mengunggah |
| `YT_PRIVACY` | `private` | Biarkan private. Ubah ke public dari YouTube Studio kalau video sudah layak |
| `YT_CHANNEL_NAME` | `AI WHAT IF?` | Nama kanal yang harus cocok dengan token |
| `TELEGRAM_ENABLED` | `true` | Notifikasi. Butuh token dan chat id |

Kunci API yang dipakai: `GEMINI_API_KEY`, `GROQ_API_KEY`, `CF_ACCOUNT_ID`, `CF_API_TOKEN`, `FAL_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.

## Tiga mode provider

### FREE SAFE (default)

- Naskah: Gemini. Kalau kuota atau billing habis, Groq hanya jika kuncinya ada. Kalau keduanya gagal, template lokal.
- Gambar: Cloudflare. Kalau gagal, cache, lalu file lokal yang namanya sama dengan adegan (`hook.jpg`, `awal.jpg`, `puncak.jpg`, `penutup.jpg`).
- Suara: Edge TTS, lalu file di `assets/fallback/audio/{adegan}.mp3`.
- fal.ai dan AI Horde tidak dipanggil.

`FREE_ONLY=true` diperiksa di kode, bukan hanya label. Menyala bersama `IMAGE_FALLBACK_ENABLED=true` tetap tidak memanggil fal.ai.

### AUTO FALLBACK

Set `PROVIDER_MODE=auto_fallback`.

- Groq ikut jika kuncinya ada.
- AI Horde ikut hanya jika `HORDE_ENABLED=true`. Antreannya bisa beberapa menit dan kuotanya tidak dijamin.
- fal.ai ikut hanya jika semua syarat ini hidup: `FREE_ONLY=false`, `PAID_FALLBACK_ENABLED=true`, `IMAGE_FALLBACK_ENABLED=true`, `FAL_KEY` terisi, modelnya punya harga yang dikenali, dan estimasinya tidak melewati `IMAGE_FALLBACK_MAX_COST_USD_PER_JOB`.

Kesalahan kuota atau billing langsung pindah. Kesalahan 5xx, timeout, dan respons kosong dicoba lagi dengan backoff, paling banyak `MAX_RETRY`. Kunci yang tidak valid tidak diulang selama sekitar 24 jam.

### LOCAL ONLY

Set `PROVIDER_MODE=local_only`, lalu jalankan dengan naskah yang sudah ada:

```powershell
.\.venv\Scripts\python main.py --uji --naskah output\folder-sebelumnya\naskah.json
```

Gambar `gambar_*.jpg` dan suara `suara_*.mp3` di folder yang sama dipakai ulang. Tidak ada panggilan Gemini, Groq, Cloudflare, Horde, fal.ai, atau Edge. Kalau aset tidak lengkap, statusnya `NEEDS_REVIEW`. Gambar acak tidak diambil.

## Batasan layanan gratis

Kuota, harga, dan nama model bisa berubah. Angka di bawah adalah perkiraan agar perencanaan harian masuk akal, bukan janji provider.

- Gemini dan Groq punya batas gratis masing-masing. Habis kuota, sistem pindah dan menulis cooldown sampai lewat tengah malam WIB.
- Cloudflare Workers AI punya jatah neuron harian. Gambar hook memakai model yang lebih boros; tiga adegan lain memakai model hemat. Lima video × 4 gambar = 20 permintaan, dan itulah batas `IMAGE_DAILY_MAX`.
- Edge TTS tidak membutuhkan kunci, tetapi tetap layanan luar. Mode lokal tidak memanggilnya.
- GitHub Actions gratis punya batas menit bulanan. Satu video kira-kira beberapa menit. Batch lima lebih aman dijalankan di laptop.
- Proyek Google Cloud yang belum diaudit biasanya hanya bisa mengunggah video **private**.

## Tes satu video

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\python main.py --cek
.\.venv\Scripts\python main.py --uji --slot pagi
```

`--uji` dan `--dry-run` tidak mengunggah dan tidak mencatat riwayat, walaupun `YT_UPLOAD=1`.

Hasil ada di `output\uji-TANGGAL-pagi-ID\`:

- `AI-WHAT-IF-TANGGAL-pagi.mp4`
- `naskah.json`, `gambar_*.jpg`, `suara_*.mp3`
- `youtube.txt`, `laporan.json`

Perintah lain:

```powershell
.\.venv\Scripts\python main.py --uji --topik "Bagaimana jika Bulan menghilang"
.\.venv\Scripts\python main.py --uji --naskah output\uji-TANGGAL-pagi-ID\naskah.json
.\.venv\Scripts\python -m unittest tests.test_fallback tests.test_whatif
```

Render ulang dari naskah yang sama memakai gambar di folder itu dan cache prompt, jadi permintaan gambar tidak diulang.

## Batch lima video

```powershell
.\.venv\Scripts\python main.py --uji --batch
.\.venv\Scripts\python main.py --batch
```

Batch berjalan berurutan. Slot yang sudah ada dilewati. Satu slot yang gagal tidak menghentikan slot berikutnya. Tanpa `--uji`, hasilnya dicatat dan ikut batas lima video hari itu.

## Jadwal

### GitHub Actions + cron-job.org

Disk runner kosong lagi di run berikutnya. Yang bertahan adalah commit ke:

- `data/history_whatif.json`
- `data/upload_ledger.json`
- `data/cooldown.json`
- `data/kuota_gambar.json`

Workflow menarik commit itu di awal, lalu mendorong perubahan di akhir. Cache Actions atau database luar tidak dipakai. Kalau commit riwayat gagal, video berikutnya bisa mengulang topik; ada pesan Telegram untuk kejadian itu.

1. Repo private. Jangan ikutkan `.env` dan `secrets/`.
2. Secrets: `GEMINI_API_KEY`, `CF_ACCOUNT_ID`, `CF_API_TOKEN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, dan `YT_TOKEN_JSON`. `GROQ_API_KEY` opsional.
3. Variables: biarkan `YT_PRIVACY` kosong atau `private`. `FREE_ONLY=true`. Jangan set `YT_UPLOAD=0` kalau upload otomatis harus jalan.
4. Tes dari tab Actions → **Video harian** → **Run workflow** → centang mode uji.
5. Di cron-job.org, zona waktu `Asia/Jakarta`. Lima job POST ke  
   `https://api.github.com/repos/USERNAME/REPO/actions/workflows/video.yml/dispatches`  
   Header: `Authorization: Bearer TOKEN`, `Accept: application/vnd.github+json`, `X-GitHub-Api-Version: 2022-11-28`, `Content-Type: application/json`.

| Jam WIB | Body |
|---|---|
| 07:00 | `{"ref":"main","inputs":{"slot":"pagi"}}` |
| 12:00 | `{"ref":"main","inputs":{"slot":"siang"}}` |
| 16:00 | `{"ref":"main","inputs":{"slot":"sore"}}` |
| 19:00 | `{"ref":"main","inputs":{"slot":"malam"}}` |
| 21:00 | `{"ref":"main","inputs":{"slot":"larut"}}` |

Token GitHub butuh izin Actions: Read and write pada repo **ini**, bukan repo kanal lama. Tes dari laptop:

```powershell
powershell -ExecutionPolicy Bypass -File .\picu_slot.ps1 -Slot pagi -Uji -Repo USERNAME/REPO
```

Dua workflow tidak berjalan bersamaan (`concurrency: ai-what-if`). Slot yang sudah tercatat tidak dibuat lagi.

### Laptop

Jangan dipasang bersamaan dengan Actions, nanti videonya dobel.

```powershell
powershell -ExecutionPolicy Bypass -File .\pasang_jadwal.ps1
powershell -ExecutionPolicy Bypass -File .\pasang_jadwal.ps1 -Hapus
```

Nama tugasnya `AI WHAT IF Pagi` dan seterusnya, terpisah dari jadwal kanal lama.

## YouTube

Upload otomatis menyala dan masuk sebagai **private**. Token kanal lama di `secrets/token.json` diabaikan. Kamu mengubah privasinya ke publik nanti dari YouTube Studio.

1. Buat proyek Google Cloud untuk kanal ini. Aktifkan YouTube Data API v3.
2. OAuth consent: tambahkan akun pengelola kanal sebagai test user, lalu publish agar tidak kedaluwarsa tiap 7 hari.
3. Buat client Desktop, simpan JSON sebagai `secrets\youtube_whatif\client_secret.json`.
4. Login sambil memilih akun yang punya kanal **AI WHAT IF?**:

```powershell
.\.venv\Scripts\python main.py --login
```

Perintah itu mencetak nama kanal dari token. Kalau bukan `AI WHAT IF?`, upload ditolak. Samakan nama kanal atau isi `YT_CHANNEL_NAME` hanya jika kamu memang yakin itu kanal yang benar.

5. Untuk Actions, salin isi `secrets\youtube_whatif\token.json` ke secret `YT_TOKEN_JSON`. Jangan menempel token kanal lama.
6. `YT_UPLOAD=1` dan `YT_PRIVACY=private` sudah cukup. Video lolos cek masuk ke YouTube sebagai private, lengkap dengan hashtag di baris pertama deskripsi.
7. Kalau videonya sudah layak, ubah privasinya ke public dari YouTube Studio. Jangan mengganti token kanal lain.

Video ditandai `containsSyntheticMedia`, dan deskripsinya menyebut narasi serta gambar bantuan AI. Ledger di `data/upload_ledger.json` menolak unggahan kedua untuk file yang sama. Kalau koneksi putus di tengah, statusnya `tidak_pasti` dan tidak diulang otomatis; cek YouTube Studio dulu, lalu hapus entri ledger itu hanya jika videonya memang tidak ada.

## Mengganti provider saat limit

```powershell
.\.venv\Scripts\python main.py --cek
```

Lalu lihat `laporan.json` di folder output: provider, alasan fallback, dan sisa gejala.

- Gemini habis: isi `GROQ_API_KEY`, atau biarkan template lokal.
- Cloudflare habis: tunggu lewat tengah malam WIB, atau taruh gambar yang sesuai di `assets\fallback\hook.jpg` (dan `awal`, `puncak`, `penutup`).
- Semua kuota habis: `PROVIDER_MODE=local_only` dan render ulang dari folder yang sudah ada.
- Jangan menyalakan fal.ai hanya dengan mengisi `FAL_KEY`. `FREE_ONLY=true` tetap memblokirnya.

Cooldown tersimpan di `data/cooldown.json`. Menghapus satu kunci provider di situ membuatnya boleh dicoba lagi.

## Error yang sering muncul

| Gejala | Yang dilakukan |
|---|---|
| `NEEDS_REVIEW` | Buka `laporan.txt`. Naskah dan aset yang sudah jadi tidak dibuang. Perbaiki, lalu `--paksa --naskah` folder itu. |
| `slot sudah dibuat` atau `batas harian` | Slot atau hari itu sudah tercatat. `--paksa` hanya jika kamu memang ingin mengganti. |
| `Slot ... sedang berjalan` | Ada proses lain. Tunggu, atau hapus `data\locks\...lock` hanya jika prosesnya sudah mati lebih dari 50 menit. |
| Gemini/Groq `quota` atau `billing` | Tidak diulang. Sistem pindah provider. Isi kunci cadangan atau pakai template. |
| `API key invalid` | Provider itu diistirahatkan sekitar 24 jam. Perbaiki kunci, lalu hapus entri cooldown-nya. |
| HTTP 429 tanpa kata kuota | Ditunda sebentar, lalu pindah kalau masih gagal. |
| HTTP 5xx atau timeout | Dicoba lagi dengan backoff, lalu fallback. |
| Gambar tidak ada | Tidak diganti gradien atau foto acak. Taruh aset bernama adegan, atau ulangi saat kuota pulih. |
| Durasi di luar 35–55 detik | Video tetap disimpan, tetapi tidak diunggah. Edit naskah dan render ulang. |
| `Login YouTube kedaluwarsa` | `--login` lagi, lalu perbarui secret `YT_TOKEN_JSON`. |
| Nama kanal tidak cocok | Upload dibatalkan. Jangan memaksa token kanal lain. |
| `Status upload tidak pasti` | Cek Studio. Jangan menjalankan upload yang sama sebelum statusnya jelas. |
| Telegram tidak menerima | `--telegram-id` setelah menekan Start di bot. Video tetap ada di folder output. |
| Actions merah | Buka log langkah **Bikin video** dan artifact `laporan.json`. |

Exit code: `0` selesai atau dilewati, `2` perlu ditinjau, `1` gagal.

## Yang sudah teruji dan yang masih manual

Teruji otomatis, tanpa kuota sungguhan dan tanpa upload publik:

- Pindah provider saat kuota, termasuk Groq setelah Gemini.
- Mode gratis tidak memanggil fal.ai atau Horde walaupun saklarnya kelihatan menyala.
- Batas video harian, slot duplikat, dan kunci proses.
- Topik yang intinya sama ditolak; topik yang hanya mirip permukaannya tidak.
- Aset lokal hanya untuk nama adegan yang cocok.
- Pemeriksaan rasio 9:16, durasi, dan satu frame 1080×1920.
- Dry-run tidak memanggil upload.
- Mode YouTube-only tidak menulis caption TikTok.
- Riwayat bisa dibaca lagi setelah disimpan.
- Kegagalan satu slot tidak menghentikan slot berikutnya.

Masih perlu kamu siapkan sendiri:

- Kunci Gemini dan Cloudflare, plus bot Telegram.
- File font `assets\fonts\PlusJakartaSans.ttf` kalau ingin font kanal. Tanpa file itu, Windows memakai Segoe dan Ubuntu memakai DejaVu.
- Login YouTube ke kanal yang benar, lalu keputusan untuk menyalakan `YT_UPLOAD`.
- Musik di `assets\music\` hanya jika lisensinya memang boleh dipakai. Tidak ada pengunduhan otomatis.
- Gambar cadangan di `assets\fallback\` kalau kamu ingin mode tanpa API tetap punya visual yang relevan.
- Jadwal cron-job.org dan secret GitHub.

Tes yang lolos tidak sama dengan video siap publik. Tonton dulu hasil `--uji` di Telegram atau di folder output.
