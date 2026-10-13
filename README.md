# KerjaPakaiAI: 3 video Shorts/TikTok per hari, otomatis

Tiga kali sehari (07:00, 12:00, dan 18:00 WIB) sistem ini:

1. Menulis naskah 35–50 detik + prompt gambar lewat Gemini (free tier)
2. Membuat 4 gambar AI untuk latar adegan lewat Cloudflare Workers AI (free tier)
3. Membuat suara Indonesia dengan Edge TTS (gratis)
4. Merender animasi 30 fps: latar zoom/geser, transisi kilat + whoosh, kata hook muncul satu per satu, prompt diketik dengan kursor, jawaban AI "sedang mengetik", efek stabilo di trik, subtitle dengan kotak sorot per kata, progress bar
5. Mengirim video + caption siap tempel ke Telegram. Upload YouTube dan TikTok tetap manual.
6. Upload ke YouTube Shorts hanya kalau `YT_UPLOAD=1` (biarkan `0` dulu)

Ide topik dipilih Gemini. Video pagi menjanjikan topik "nanti siang", siang menjanjikan "nanti sore", sore menjanjikan "besok", dan topik itu yang benar-benar dibuat berikutnya. Tiga video dalam satu hari selalu beda kategori.

| Hari | Pagi | Siang | Sore |
|---|---|---|---|
| Senin | Excel & Data | Jualan Online | Cari Kerja |
| Selasa | Email & Chat Kerja | Rapat & Laporan | Belajar & Tugas |
| Rabu | Jualan Online | Cari Kerja | Produktivitas |
| Kamis | Rapat & Laporan | Belajar & Tugas | Excel & Data |
| Jumat | Cari Kerja | Produktivitas | Email & Chat Kerja |
| Sabtu | Belajar & Tugas | Excel & Data | Jualan Online |
| Minggu | Produktivitas + rekap minggu | Email & Chat Kerja | Rapat & Laporan |

Semua layanan di atas dipakai di dalam batas gratisnya: 3 naskah, 12 gambar (sekitar 4.000 neuron Cloudflare dari kuota 10.000 per hari), dan ±450 menit GitHub Actions per bulan.

---

## Langkah 1: Akun yang dibutuhkan

| Layanan | Untuk apa | Status |
|---|---|---|
| Gemini API | Naskah | Sudah (key ada di `.env`) |
| Cloudflare | Gambar AI | Langkah 2 |
| Telegram bot | Kirim video ke HP | Langkah 3 |
| GitHub | Menjalankan otomatis walau laptop mati | Langkah 5 |
| Google Cloud (YouTube) | Upload otomatis, opsional | Langkah 6 |

## Langkah 2: Cloudflare Workers AI (gambar, gratis)

1. Daftar di https://dash.cloudflare.com/sign-up (gratis, tanpa kartu kredit)
2. **Account ID:** di dashboard, klik nama akun kamu → menu titik tiga di samping nama akun → **Copy account ID**. Atau buka **Workers & Pages**, Account ID ada di panel kanan
3. **API token:** klik ikon profil (kanan atas) → **Profile** → **API Tokens** → **Create Token** → pilih template **Workers AI** → **Continue to summary** → **Create Token** → salin tokennya
4. Isi di `.env`:
   ```
   CF_ACCOUNT_ID=...
   CF_API_TOKEN=...
   ```

Kuota gratis 10.000 "neuron" per hari; 12 gambar per hari memakai sekitar 4.000 neuron.

## Langkah 3: Bot Telegram

1. Di Telegram, buka **@BotFather**, kirim `/newbot`, ikuti instruksinya (nama bebas, username harus diakhiri `bot`)
2. Salin token yang diberikan, isi `TELEGRAM_BOT_TOKEN=...` di `.env`
3. Buka bot kamu, tekan **Start**, kirim pesan apa saja
4. Ambil chat ID:
   ```powershell
   .\.venv\Scripts\python main.py --telegram-id
   ```
   Salin baris `TELEGRAM_CHAT_ID=...` ke `.env`

Kalau ada error, bot ini juga mengirim pesan "GAGAL ..." ke kamu.

## Langkah 4: Tes di laptop

```powershell
.\.venv\Scripts\python main.py --uji --slot pagi
```

Hasilnya di `output\uji-TANGGAL-pagi\` (dan terkirim ke Telegram kalau Langkah 3 sudah):

- `KerjaPakaiAI-TANGGAL-pagi.mp4`: videonya
- `naskah.json`: naskah lengkap, bisa diedit lalu render ulang dengan `--naskah`
- `gambar_*.jpg`: gambar AI per adegan
- `youtube.txt` dan `caption_tiktok.txt`

Perintah lain:

```powershell
# Paksa topik tertentu
.\.venv\Scripts\python main.py --uji --topik "Rumus VLOOKUP untuk cocokkan data"

# Render ulang dari naskah yang sudah diedit
.\.venv\Scripts\python main.py --uji --naskah output\uji-2026-10-13-pagi\naskah.json

# Video beneran (dicatat di riwayat supaya topik nyambung)
.\.venv\Scripts\python main.py --slot pagi
```

Satu video makan waktu ±3–5 menit (naskah, gambar, render).

## Langkah 5: Otomatis di GitHub Actions (laptop boleh mati)

### 5a. Upload project ke GitHub

1. Daftar di https://github.com/signup
2. Klik **New repository**, nama misalnya `kerjapakaiai`, pilih **Private**, jangan centang README, klik **Create repository**
3. Di terminal folder ini (ganti `USERNAME`):
   ```powershell
   git init -b main
   git add .
   git commit -m "KerjaPakaiAI"
   git remote add origin https://github.com/USERNAME/kerjapakaiai.git
   git push -u origin main
   ```
   Saat push pertama, jendela login GitHub akan muncul.

File `.env`, folder `secrets\`, dan `output\` tidak ikut terupload (sudah ada di `.gitignore`).

### 5b. Isi secrets

Di repo GitHub: **Settings → Secrets and variables → Actions**.

Tab **Secrets** → **New repository secret**, isi satu per satu (nilainya sama dengan di `.env`):

- `GEMINI_API_KEY`
- `CF_ACCOUNT_ID`
- `CF_API_TOKEN`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `YT_TOKEN_JSON` (opsional, lihat Langkah 6)

Tab **Variables** (opsional): `YT_UPLOAD` = `1` kalau mau upload YouTube, `YT_PRIVACY` = `private`/`unlisted`/`public`.

### 5c. Tes sekali

Tab **Actions** → **Video harian** → **Run workflow** → centang **Mode uji** → **Run workflow**. Tunggu ±5 menit; video masuk ke Telegram, dan bisa juga diunduh dari bagian **Artifacts** di halaman run.

Setelah itu jadwal berjalan sendiri tiap 07:00, 12:00, dan 18:00 WIB. GitHub kadang menunda jadwal 5–30 menit, itu normal. Setiap run mencatat riwayat topik ke `data/history.json` di repo. Kalau repo tidak ada aktivitas selama 60 hari, GitHub mematikan jadwal ini; commit riwayat menjaga jadwalnya tetap hidup.

## Langkah 6: Upload otomatis ke YouTube (opsional)

Penting: proyek Google Cloud yang **belum diaudit** hanya bisa upload sebagai **private**. Pilihannya:

- Biarkan private, lalu buka link YouTube Studio yang dikirim ke Telegram dan ubah ke Public (satu klik), atau
- Ajukan audit gratis lewat [formulir YouTube API](https://support.google.com/youtube/contact/yt_api_form). Setelah disetujui, set `YT_PRIVACY=public`.

Setup (sekali, ±10 menit):

1. Buka https://console.cloud.google.com, buat project baru, misalnya `KerjaPakaiAI`
2. **APIs & Services → Library**, cari **YouTube Data API v3**, klik **Enable**
3. **Google Auth Platform** (atau **OAuth consent screen**):
   - Isi nama aplikasi dan email, pilih **External**
   - Di **Audience**, tambahkan email Google kamu sebagai **Test user**
   - Klik **Publish app** supaya statusnya *In production*. Kalau tetap *Testing*, login kedaluwarsa tiap 7 hari. Peringatan "aplikasi belum diverifikasi" saat login itu normal; klik **Advanced → Go to ...**
4. **Clients → Create client**, tipe **Desktop app**, **Download JSON**, simpan sebagai `secrets\client_secret.json`
5. Login sekali (browser terbuka, pilih akun yang punya channel):
   ```powershell
   .\.venv\Scripts\python main.py --login
   ```
6. Untuk laptop: set `YT_UPLOAD=1` di `.env`
7. Untuk GitHub Actions: buka `secrets\token.json`, salin seluruh isinya ke secret `YT_TOKEN_JSON`, lalu set variable `YT_UPLOAD` = `1`

Video ditandai sebagai konten buatan AI (`containsSyntheticMedia`) sesuai aturan YouTube.

## Alternatif: jalan di laptop

Kalau tidak mau pakai GitHub, pasang jadwal Windows (laptop harus menyala):

```powershell
powershell -ExecutionPolicy Bypass -File .\pasang_jadwal.ps1
# jam lain:
powershell -ExecutionPolicy Bypass -File .\pasang_jadwal.ps1 -JamPagi 06:30 -JamSiang 12:30 -JamSore 17:00
# hapus:
powershell -ExecutionPolicy Bypass -File .\pasang_jadwal.ps1 -Hapus
```

Kalau jadwal lama (pagi dan sore saja) sudah terpasang, jalankan perintah yang sama sekali lagi supaya slot siang ikut terdaftar.

Jangan pakai dua-duanya sekaligus, nanti videonya dobel dan riwayatnya tidak sinkron.

## Musik latar (opsional)

Taruh file `.mp3` di `assets\music\` (dan commit ke GitHub kalau pakai Actions). Satu lagu dipilih acak, volumenya di bawah suara. Ambil dari YouTube Studio → **Audio Library** dan pastikan lisensinya boleh dipakai di luar YouTube kalau mau dipost ke TikTok.

## Mengubah tampilan dan isi

- **Kategori:** `KATEGORI` di `kpai/config.py`
- **Gaya naskah:** `_instruksi` di `kpai/script_gen.py`
- **Gaya gambar:** `IMAGE_STYLE` di `.env` (misalnya ganti ke `3D pixar style illustration, ...`)
- **Warna (5 tema, berganti tiap video):** `TEMA` di `kpai/render.py`
- **Animasi tiap adegan:** fungsi `_hook`, `_prompt`, `_hasil`, `_trik`, `_penutup` di `kpai/render.py`
- **Suara:** `TTS_VOICE` dan `TTS_RATE` di `.env`

## Kalau ada masalah

| Gejala | Solusi |
|---|---|
| Gemini 503 / high demand | Otomatis pindah ke model cadangan (`GEMINI_MODEL_CADANGAN`) |
| Gemini 429 / quota | Batas free tier habis sementara, coba lagi nanti |
| Latar cuma gradien, bukan gambar | Cloudflare belum diisi atau gagal; cek `CF_ACCOUNT_ID` / `CF_API_TOKEN` |
| Telegram tidak menerima video | Pastikan sudah menekan Start di bot, dan `TELEGRAM_CHAT_ID` benar (`--telegram-id`) |
| Telegram `CERTIFICATE_VERIFY_FAILED` / "not trusted" | Jaringan kantor memblokir Telegram. Video tetap jadi; di GitHub Actions Telegram jalan normal |
| `Login YouTube kedaluwarsa` | Jalankan `--login` lagi, perbarui secret `YT_TOKEN_JSON`; pastikan app *In production* |
| Run GitHub gagal | Tab Actions → klik run yang merah → lihat langkah yang gagal |
| "sudah dibuat" | Slot itu sudah ada di riwayat; pakai `--paksa` untuk bikin ulang |

## Catatan monetisasi

- Syarat YouTube Partner Program: 1.000 subscriber + 10 juta tayangan Shorts dalam 90 hari, atau 4.000 jam tayang video panjang
- YouTube menolak monetisasi konten yang "diproduksi massal / repetitif". Yang membedakan channel ini: tiap video berisi prompt yang benar-benar bisa dipakai. Di minggu-minggu awal, cek video di Telegram sebelum dipublikasikan
- Uang tercepat biasanya dari link affiliate tool AI dan produk digital (kumpulan prompt) di deskripsi, bukan dari iklan Shorts
