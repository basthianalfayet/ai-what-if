"""Naskah cadangan kalau Gemini dan Groq sama-sama tidak bisa dipakai."""

TOPIK = {
    "Excel & Data": "Rumus untuk mencocokkan dua tabel",
    "Email & Chat Kerja": "Membalas email atasan yang mendesak",
    "Jualan Online": "Membalas komplain pembeli dengan sopan",
    "Rapat & Laporan": "Mengubah catatan rapat jadi notulen",
    "Cari Kerja": "Merapikan pengalaman kerja untuk CV",
    "Belajar & Tugas": "Merangkum materi panjang jadi poin",
    "Produktivitas": "Menyusun prioritas tugas hari ini",
}

TOPIK_CADANGAN = {
    "Excel & Data": "Membersihkan data yang dobel di sheet",
    "Email & Chat Kerja": "Menolak permintaan lewat chat kerja",
    "Jualan Online": "Menulis deskripsi produk yang jelas",
    "Rapat & Laporan": "Menyusun laporan mingguan yang singkat",
    "Cari Kerja": "Menyiapkan jawaban interview yang jujur",
    "Belajar & Tugas": "Mengubah bacaan sulit jadi contoh",
    "Produktivitas": "Memecah tugas besar jadi langkah kecil",
}


def template_lokal(kategori, kategori_besok, label_berikut, topik=None):
    from .script_gen import Naskah, rapikan

    nama = kategori[0]
    nama_besok = kategori_besok[0]
    topik = (topik or TOPIK[nama]).strip()
    topik_besok = TOPIK[nama_besok]
    if topik.lower() == topik_besok.lower():
        topik_besok = TOPIK_CADANGAN[nama_besok]

    prompt = (
        f"Kamu asisten untuk {nama}. Selesaikan tugas ini: {topik}. "
        "Gunakan data di [placeholder] dan jangan mengarang angka atau fakta yang tidak tertulis di situ. "
        "Jawaban bahasa Indonesia, maksimal lima poin, tiap poin satu kalimat, "
        "lalu tutup dengan satu langkah yang bisa dikerjakan dalam sepuluh menit."
    )
    hasil = (
        f"Kerangka untuk {topik}:\n"
        "- Sebutkan data yang sudah ada di catatan\n"
        "- Tandai bagian yang masih kosong dan perlu ditanyakan\n"
        "- Urutkan langkah dari yang paling cepat selesai\n"
        "- Tulis hasil akhir dengan bahasa yang bisa langsung dipakai"
    )
    return rapikan(Naskah(
        topik=topik,
        judul=f"{topik[:52]} pakai prompt ini",
        deskripsi=(
            f"Video ini memberi satu prompt untuk {topik.lower()}. "
            "Salin prompt di layar, isi data kamu pada bagian kurung, lalu kirim ke AI."
        ),
        tags=["prompt ai", "tips kerja", nama.lower(), "chatgpt", "produktivitas"],
        hook=f"Masih keteter kalau harus bereskan {topik.lower()} sendirian?",
        narasi_prompt=(
            "Tenang. Prompt di layar ini sudah disusun supaya AI mengerjakan bagian yang menghabiskan waktumu. "
            "Salin, lalu isi bagian yang bertanda kurung dengan data kamu."
        ),
        prompt=prompt,
        narasi_hasil=(
            "Hasilnya bukan janji kosong. AI memecah pekerjaan itu jadi poin yang bisa langsung dikerjakan, "
            "memisahkan yang sudah jelas dan yang masih perlu data dari kamu. "
            "Kamu tinggal menyalin bagian yang pas."
        ),
        hasil=hasil,
        narasi_trik=(
            "Sebelum mengirim prompt, tempel juga kalimat trik di akhir biar AI tidak mengisi kekosongan dengan karangan."
        ),
        trik="Kalau ada angka, tanggal, atau nama, gunakan persis seperti di data dan jangan dibulatkan.",
        topik_besok=topik_besok,
        penutup=f"Simpan video ini supaya promptnya tidak hilang. {label_berikut} kita bahas {topik_besok}.",
        gambar_hook=f"stressed Indonesian worker facing the problem of {topik}, cinematic office, no readable text",
        gambar_kerja="close-up of hands typing a prompt on a laptop in a Jakarta workspace, warm light, no readable screen text",
        gambar_trik="relieved Indonesian professional smiling at a tidy desk after finishing work, bright natural light",
        gambar_penutup=f"Indonesian workspace prepared for the next topic {topik_besok}, morning light, no readable text",
    ))
