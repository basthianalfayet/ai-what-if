"""Naskah lokal kalau Gemini dan Groq tidak bisa dipakai. Isinya skenario fiksi yang sengaja hati-hati."""

from .topik import mirip_dengan_daftar

BANK = {
    "Luar Angkasa": [
        {
            "topik": "Matahari tiba-tiba menghilang",
            "inti": "matahari hilang",
            "judul_kerja": "Jika Matahari menghilang",
            "hook": "Bagaimana jika Matahari tiba-tiba menghilang? Cahaya yang kamu lihat sekarang baru tiba sekitar delapan menit kemudian.",
            "adegan": [
                ("Bagaimana jika Matahari menghilang?", "Langit masih terang sebentar, lalu gelap.", "cinematic earth sky at the last moment of sunlight, vertical, no text"),
                ("Dalam skenario fiksi ini, setelah cahaya terakhir sampai, Bumi kehilangan sumber energi utamanya. Suhu tidak runtuh dalam hitungan detik karena lautan dan udara masih menyimpan panas.", "Bumi yang mulai gelap, laut masih menyimpan panas.", "cinematic darkening earth from space with glowing oceans, vertical, no text"),
                ("Tanaman lalu kehilangan cahaya untuk fotosintesis, dan rantai makanan ikut goyah. Orbit Bumi tidak serta-merta jatuh ke titik kosong. Yang hilang dalam cerita ini adalah panas dan cahaya, bukan lantai di bawah kakimu.", "Tanaman meredup dan orbit bumi tetap melengkung.", "cinematic wilted forest under a star filled sky, vertical, no text"),
                ("Ini skenario, bukan ramalan. Matahari tidak bisa lenyap begitu saja menurut fisika yang kita pahami. Menurutmu, yang lebih dulu terasa: gelapnya langit atau dingin yang datang pelan?", "Bumi kecil di langit tanpa matahari.", "cinematic lonely earth in starfield, soft light, vertical, no text"),
            ],
            "penjelasan": "Cahaya Matahari butuh sekitar delapan menit untuk sampai ke Bumi. Lautan menyimpan panas, jadi pendinginan tidak seperti saklar yang dimatikan. Fotosintesis memang bergantung pada cahaya.",
            "batas": "Tidak ada mekanisme yang diketahui yang membuat Matahari lenyap seketika. Angka pendinginan yang beredar di internet sering terlalu cepat dan tidak dipakai di video ini.",
            "ending": "Ini skenario, bukan ramalan. Matahari tidak bisa lenyap begitu saja menurut fisika yang kita pahami.",
            "tanya": "Menurutmu, yang lebih dulu terasa: gelapnya langit atau dingin yang datang pelan?",
            "judul": "Bagaimana jika Matahari tiba-tiba menghilang?",
            "deskripsi": "Skenario fiksi tentang Bumi yang kehilangan cahaya Matahari. Videonya memisahkan akibat yang masuk akal dari bagian yang tidak mungkin.",
            "tag": ["matahari", "what if", "luar angkasa", "sains", "shorts"],
            "sumber": ["Waktu tempuh cahaya Matahari ke Bumi sekitar delapan menit adalah pengetahuan fisika dasar."],
        },
        {
            "topik": "Bulan menjauh dari Bumi",
            "inti": "bulan menjauh",
            "judul_kerja": "Jika Bulan pergi",
            "hook": "Bagaimana jika Bulan perlahan pergi menjauh sampai pasang laut nyaris hilang dari pantai yang biasa kamu lihat?",
            "adegan": [
                ("Bagaimana jika Bulan pergi jauh?", "Pantai senja tanpa bulan di langit.", "cinematic empty night beach with no moon, vertical, no text"),
                ("Dalam skenario ini, tarikan Bulan yang melemah membuat pasang laut jauh lebih kecil. Banyak pantai kehilangan ritme naik turun yang sekarang membentuk ekosistem pesisir.", "Air laut yang tenang tanpa garis pasang.", "cinematic calm shoreline at night, vertical, no text"),
                ("Hewan yang bertelur mengikuti siklus pasang bisa kehilangan isyarat waktu. Sumbu Bumi juga bisa lebih goyang tanpa penstabil Bulan, tetapi seberapa kacau iklimnya tidak bisa dipastikan dari cerita pendek.", "Penyu di pantai gelap mencari air.", "cinematic sea turtle on a dark beach, vertical, no text"),
                ("Bulan memang sudah menjauh sedikit demi sedikit, tetapi tidak sedang kabur minggu ini. Kalau pasang laut mengecil, ekosistem pantai mana yang menurutmu paling berubah?", "Bulan kecil di kejauhan di atas bumi.", "cinematic tiny moon far above earth, vertical, no text"),
            ],
            "penjelasan": "Pasang laut di Bumi terutama dipengaruhi gravitasi Bulan dan juga Matahari. Bulan saat ini menjauh sekitar beberapa sentimeter per tahun, bukan menghilang dalam semalam.",
            "batas": "Dampak iklim jika Bulan jauh lebih kecil di langit adalah model yang rumit. Video ini tidak memberi angka suhu atau tahun kepunahan.",
            "ending": "Bulan memang sudah menjauh sedikit demi sedikit, tetapi tidak sedang kabur minggu ini.",
            "tanya": "Kalau pasang laut mengecil, ekosistem pantai mana yang menurutmu paling berubah?",
            "judul": "Bagaimana jika Bulan pergi menjauh?",
            "deskripsi": "Skenario fiksi tentang pasang laut dan pantai jika Bulan jauh lebih jauh. Bukan jadwal kejadian nyata.",
            "tag": ["bulan", "pasang laut", "what if", "bumi", "shorts"],
            "sumber": ["Pasang laut terkait gravitasi Bulan adalah pengetahuan astronomi dasar."],
        },
    ],
    "Bumi dan Alam": [
        {
            "topik": "Bumi berhenti berputar lima detik",
            "inti": "bumi berhenti putar",
            "judul_kerja": "Jika Bumi berhenti lima detik",
            "hook": "Bagaimana jika Bumi berhenti berputar selama lima detik, lalu berputar lagi seperti tidak terjadi apa-apa?",
            "adegan": [
                ("Bagaimana jika Bumi berhenti berputar?", "Kota yang terdorong ke arah timur.", "cinematic city street with motion blur at sunrise, vertical, no text"),
                ("Permukaan Bumi di khatulistiwa bergerak ratusan meter per detik. Kalau tanah berhenti dan kamu tidak, tubuh, laut, dan udara masih membawa kecepatan itu. Lima detik sudah cukup untuk membuat kekacauan besar.", "Ombak raksasa masuk ke daratan.", "cinematic enormous wave approaching a coast, vertical, no text"),
                ("Bagian yang sering dilewatkan: atmosfer ikut bergerak. Angin ekstrem dan air laut yang bergeser lebih menentukan daripada sensasi diam sejenak. Angka pastinya bergantung pada bagaimana berhentinya dimodelkan, dan model itu sendiri tidak nyata.", "Awan terkoyak di atas benua.", "cinematic violent clouds over a continent from above, vertical, no text"),
                ("Bumi tidak berhenti berputar. Cerita ini hanya menunjukkan betapa besar momentum yang sekarang terasa biasa. Menurutmu, laut atau udara yang lebih dulu terasa kacau?", "Bumi berputar tenang dilihat dari orbit.", "cinematic peaceful rotating earth from orbit, vertical, no text"),
            ],
            "penjelasan": "Di khatulistiwa, permukaan Bumi bergerak sekitar 1.670 kilometer per jam relatif terhadap sumbu rotasi. Menghentikan tanah tidak otomatis menghentikan laut dan udara yang sudah bergerak.",
            "batas": "Tidak ada gaya yang diketahui yang bisa menghentikan rotasi Bumi lima detik lalu menyalakannya lagi. Kerusakan rincinya tidak dihitung sebagai ramalan.",
            "ending": "Bumi tidak berhenti berputar. Cerita ini hanya menunjukkan momentum yang sekarang terasa biasa.",
            "tanya": "Menurutmu, laut atau udara yang lebih dulu terasa kacau?",
            "judul": "Bagaimana jika Bumi berhenti berputar lima detik?",
            "deskripsi": "Skenario fiksi tentang momentum laut dan udara jika rotasi Bumi berhenti sesaat. Bukan peringatan bencana.",
            "tag": ["bumi", "rotasi", "what if", "fisika", "shorts"],
            "sumber": ["Kecepatan rotasi di khatulistiwa sekitar 1.670 kilometer per jam adalah pengetahuan ilmu bumi dasar."],
        },
        {
            "topik": "Oksigen di udara menjadi dua kali lipat",
            "inti": "oksigen dua kali",
            "judul_kerja": "Jika oksigen berlipat dua",
            "hook": "Bagaimana jika kadar oksigen di udara menjadi dua kali lipat dalam satu malam, tanpa ada yang memindahkan gunung?",
            "adegan": [
                ("Bagaimana jika oksigen berlipat ganda?", "Hutan basah dengan udara yang terasa terlalu ramai.", "cinematic dense rainforest at dawn, vertical, no text"),
                ("Napas terasa lebih mudah di awal cerita, tetapi oksigen yang lebih kaya juga membuat api lebih mudah menyala. Hutan yang lembap sekalipun menjadi lebih berisiko saat ada petir.", "Percikan api di antara pohon.", "cinematic lightning spark in a forest, vertical, no text"),
                ("Serangga yang bergantung pada difusi udara bisa tumbuh dalam batas tertentu, seperti yang dibahas untuk zaman oksigen tinggi di masa lalu. Tubuh manusia tidak otomatis menjadi super. Paru-paru dan jaringan punya batasnya sendiri.", "Serangga besar di daun basah, tetap realistis.", "cinematic large dragonfly on a wet leaf, photoreal, vertical, no text"),
                ("Kadar oksigen bumi tidak melonjak semalam. Yang menarik justru betapa sempit rentang udara yang kita anggap biasa. Menurutmu, api atau napas yang lebih dulu berubah?", "Nyala api kecil di udara senja.", "cinematic small campfire in blue dusk, vertical, no text"),
            ],
            "penjelasan": "Udara yang kita hirup sekarang sekitar 21 persen oksigen. Api memang lebih mudah berkobar jika oksigen lebih banyak. Catatan fosil mengaitkan oksigen yang lebih tinggi di masa lalu dengan serangga yang lebih besar, tetapi sebabnya tidak hanya satu.",
            "batas": "Video ini tidak mengklaim manusia akan bernapas dua kali lebih kuat atau serangga sebesar mobil. Ambang racun oksigen dan perubahan iklim lokal tidak dihitung di sini.",
            "ending": "Kadar oksigen Bumi tidak melonjak semalam. Rentang udara yang kita anggap biasa ternyata sempit.",
            "tanya": "Menurutmu, api atau napas yang lebih dulu berubah?",
            "judul": "Bagaimana jika oksigen di udara berlipat dua?",
            "deskripsi": "Skenario fiksi tentang api, napas, dan serangga jika oksigen udara jauh lebih tinggi. Bukan prediksi.",
            "tag": ["oksigen", "atmosfer", "what if", "bumi", "shorts"],
            "sumber": ["Komposisi udara sekitar 21 persen oksigen adalah pengetahuan kimia atmosfer dasar."],
        },
    ],
    "Tubuh Manusia": [
        {
            "topik": "Manusia bisa bernapas di dalam air",
            "inti": "napas dalam air",
            "judul_kerja": "Jika manusia bernapas di air",
            "hook": "Bagaimana jika manusia bisa bernapas di dalam air, tetapi paru-paru tetap harus menukar gas, bukan menjadi insang ajaib?",
            "adegan": [
                ("Bagaimana jika manusia bernapas di air?", "Penyelam di air jernih tanpa gelembung tabung.", "cinematic diver in clear blue water, no scuba tank, vertical, no text"),
                ("Air mengandung jauh lebih sedikit oksigen daripada udara. Supaya cukup, permukaan penukar gas di tubuh harus sangat luas, atau kita harus menggerakkan air dalam volume yang besar setiap menit.", "Close-up aliran air di sekitar dada.", "cinematic close-up of water flowing around a human chest, vertical, no text"),
                ("Air juga lebih rapat, jadi usaha menariknya habis-habisan. Suhu laut menarik panas tubuh lebih cepat daripada udara. Bisa bernapas belum berarti bisa tinggal lama tanpa kedinginan dan tanpa tekanan di kedalaman.", "Siluet manusia di laut yang semakin gelap.", "cinematic human silhouette descending into dark blue water, vertical, no text"),
                ("Tidak ada manusia yang bernapas di air. Cerita ini hanya menunjukkan mengapa insang tidak bisa ditempel begitu saja. Menurutmu, oksigen atau dingin yang lebih dulu menghentikanmu?", "Permukaan laut dari bawah, cahaya di atas.", "cinematic underwater view looking up at the bright surface, vertical, no text"),
            ],
            "penjelasan": "Oksigen terlarut di air jauh lebih rendah daripada oksigen di udara. Insang ikan bekerja karena luas dan karena air terus dialirkan. Air juga menghantarkan panas tubuh lebih cepat.",
            "batas": "Video ini tidak menjanjikan teknologi insang buatan. Tekanan di kedalaman dan risiko air masuk ke paru-paru tidak disederhanakan menjadi solusi.",
            "ending": "Tidak ada manusia yang bernapas di air. Insang tidak bisa ditempel begitu saja pada tubuh kita.",
            "tanya": "Menurutmu, oksigen atau dingin yang lebih dulu menghentikanmu?",
            "judul": "Bagaimana jika manusia bisa bernapas di dalam air?",
            "deskripsi": "Skenario fiksi tentang batas oksigen terlarut dan panas tubuh jika manusia mencoba bernapas di air.",
            "tag": ["tubuh manusia", "napas", "laut", "what if", "shorts"],
            "sumber": ["Oksigen terlarut dalam air lebih rendah daripada di udara adalah pengetahuan biologi dasar."],
        },
        {
            "topik": "Manusia tidak perlu tidur sama sekali",
            "inti": "tanpa tidur",
            "judul_kerja": "Jika manusia tidak tidur",
            "hook": "Bagaimana jika manusia tidak perlu tidur sama sekali, tetapi otak tetap harus membereskan kerja sehari-hari?",
            "adegan": [
                ("Bagaimana jika tidur tidak diperlukan?", "Kota jam tiga pagi yang tetap ramai dan terang.", "cinematic quiet city at 3am still fully awake, vertical, no text"),
                ("Jam tambahan tidak otomatis menjadi waktu jernih. Tidur terkait dengan ingatan, suasana hati, dan perbaikan sel. Menghapus tidur dari cerita ini berarti tubuh perlu jalur lain untuk pekerjaan yang sama.", "Seseorang menatap jendela sebelum fajar.", "cinematic person awake by a window before dawn, vertical, no text"),
                ("Dalam beberapa hari tanpa tidur, perhatian manusia memang menurun. Itu pengamatan yang sudah dikenal, bukan efek spesial film. Kalau tidur hilang untuk selamanya, kita tidak tahu sistem penggantinya, dan video ini tidak mengarang hormon ajaib.", "Mata lelah dalam cahaya lampu.", "cinematic tired eyes in warm lamp light, photoreal, vertical, no text"),
                ("Manusia tetap perlu tidur. Pertanyaan yang lebih jujur: kalau kamu dapat empat jam ekstra, pekerjaan apa yang sebenarnya layak mengisinya?", "Tempat tidur kosong di kamar pagi.", "cinematic empty bed in morning light, vertical, no text"),
            ],
            "penjelasan": "Kurang tidur dalam jangka pendek terkait dengan perhatian yang menurun dan suasana hati yang lebih buruk. Tidur juga dikaitkan dengan konsolidasi ingatan, walaupun rincian mekanismenya masih diteliti.",
            "batas": "Video ini tidak menyebut jumlah jam ajaib atau obat yang menghapus kebutuhan tidur. Akibat seumur hidup tanpa tidur tidak bisa disimpulkan dari cerita.",
            "ending": "Manusia tetap perlu tidur. Jam tambahan tidak otomatis menjadi waktu yang jernih.",
            "tanya": "Kalau kamu dapat empat jam ekstra, pekerjaan apa yang layak mengisinya?",
            "judul": "Bagaimana jika manusia tidak perlu tidur?",
            "deskripsi": "Skenario fiksi tentang harga perhatian dan ingatan jika tidur dihapus. Bukan saran kesehatan.",
            "tag": ["tidur", "otak", "what if", "tubuh", "shorts"],
            "sumber": ["Kaitan kurang tidur dengan perhatian adalah pengetahuan kesehatan yang sudah luas, bukan angka baru."],
        },
    ],
    "Hewan": [
        {
            "topik": "Lebah menghilang dari Bumi",
            "inti": "lebah hilang",
            "judul_kerja": "Jika lebah menghilang",
            "hook": "Bagaimana jika lebah menghilang tahun ini? Bukan semua makanan lenyap besok, tetapi sebagian tanaman kehilangan penyerbuknya.",
            "adegan": [
                ("Bagaimana jika lebah menghilang?", "Kebun buah yang sepi tanpa lebah.", "cinematic orchard with empty blossoms and no bees, vertical, no text"),
                ("Banyak buah dan sayur bergantung pada serangga penyerbuk, dan lebah adalah bagian besar dari pekerjaan itu. Padi, gandum, dan jagung terutama dibantu angin, jadi semangkuk nasi tidak otomatis hilang.", "Butir padi tertiup angin.", "cinematic rice grains in the wind, vertical, no text"),
                ("Yang menyempit lebih dulu adalah ragam makanan: apel, almond, dan banyak sayuran buah. Hewan lain yang ikut menyerbuki tidak selalu sanggup menggantikan volume yang sama. Seberapa cepat panen jatuh berbeda di tiap wilayah.", "Buah almond di cabang yang sepi.", "cinematic almond branch without insects, vertical, no text"),
                ("Lebah tidak sedang menghilang semuanya minggu ini, walaupun banyak koloni memang tertekan. Kalau satu penyerbuk pergi, makanan mana yang paling kamu rindukan?", "Sarung tangan petani di antara bunga.", "cinematic farmer hands among blossoms at sunrise, vertical, no text"),
            ],
            "penjelasan": "Sebagian tanaman pangan pokok diserbuki angin. Banyak buah dan kacang bergantung pada serangga. Lebah madu dan lebah liar bukan satu-satunya penyerbuk, tetapi perannya besar di pertanian.",
            "batas": "Video ini tidak mengatakan manusia akan kelaparan dalam setahun. Angka persentase panen global sering disederhanakan berlebihan dan tidak dipakai di sini.",
            "ending": "Lebah tidak lenyap semuanya minggu ini, walaupun banyak koloni memang tertekan.",
            "tanya": "Kalau satu penyerbuk pergi, makanan mana yang paling kamu rindukan?",
            "judul": "Bagaimana jika lebah menghilang dari Bumi?",
            "deskripsi": "Skenario fiksi tentang penyerbukan jika lebah pergi. Makanan pokok tidak disamakan dengan buah yang bergantung pada serangga.",
            "tag": ["lebah", "penyerbukan", "what if", "hewan", "shorts"],
            "sumber": ["Peran serangga penyerbuk pada banyak buah adalah pengetahuan ekologi dasar."],
        },
        {
            "topik": "Paus biru menghilang dari laut",
            "inti": "paus biru hilang",
            "judul_kerja": "Jika paus biru pergi",
            "hook": "Bagaimana jika paus biru menghilang dari laut? Bukan hanya hewan besar yang hilang dari kartu pos.",
            "adegan": [
                ("Bagaimana jika paus biru pergi?", "Laut dalam yang kosong dan biru.", "cinematic empty deep blue ocean, vertical, no text"),
                ("Paus biru memakan krill dalam jumlah besar, lalu kotorannya mengembalikan nutrisi ke permukaan. Dalam skenario ini, putaran nutrisi di sebagian laut menjadi lebih sepi.", "Kawanan krill di air terang.", "cinematic krill swarm in sunlit water, vertical, no text"),
                ("Efeknya tidak sama di setiap samudra, dan hewan lain ikut bermain dalam jaring makanan yang sama. Menghapus satu spesies raksasa mengubah pola, tetapi tidak otomatis mengosongkan seluruh laut dalam satu musim.", "Permukaan laut dengan plankton hijau tipis.", "cinematic thin plankton bloom on the ocean surface, vertical, no text"),
                ("Paus biru masih ada, walaupun populasinya pernah jatuh karena perburuan. Menurutmu, hewan laut yang mana yang paling diam-diam menopang air di sekitarmu?", "Siluet paus jauh di bawah permukaan.", "cinematic distant whale silhouette underwater, vertical, no text"),
            ],
            "penjelasan": "Paus besar memindahkan nutrisi saat makan di kedalaman dan buang air di dekat permukaan. Peran itu disebut pompa paus dalam diskusi ekologi laut, dan besarnya berbeda antar wilayah.",
            "batas": "Video ini tidak menghitung ton karbon atau menjanjikan laut mati. Jaring makanan terlalu saling terkait untuk satu angka tunggal.",
            "ending": "Paus biru masih ada, walaupun populasinya pernah jatuh karena perburuan.",
            "tanya": "Menurutmu, hewan laut mana yang diam-diam paling menopang perairan di sekitarmu?",
            "judul": "Bagaimana jika paus biru menghilang?",
            "deskripsi": "Skenario fiksi tentang nutrisi laut jika paus biru tidak ada. Bukan laporan kepunahan.",
            "tag": ["paus", "laut", "what if", "hewan", "shorts"],
            "sumber": ["Peran paus dalam daur nutrisi laut dibahas dalam ekologi kelautan, tanpa angka baru di video ini."],
        },
    ],
    "Fisika": [
        {
            "topik": "Gravitasi menjadi dua kali lebih kuat",
            "inti": "gravitasi dua kali",
            "judul_kerja": "Jika gravitasi berlipat dua",
            "hook": "Bagaimana jika gravitasi Bumi menjadi dua kali lebih kuat mulai pagi ini, sementara ukuran planetnya tetap?",
            "adegan": [
                ("Bagaimana jika gravitasi menjadi dua kali?", "Orang yang langkahnya berat di trotoar.", "cinematic person walking heavily on a city sidewalk, vertical, no text"),
                ("Berat badanmu terasa dua kali, bukan massa tubuhmu. Bangunan, pohon, dan aliran darah menghadapi beban yang sama. Sebagian struktur yang sekarang cukup kuat menjadi terlalu ringan untuk dunia yang baru.", "Jembatan yang melengkung pelan.", "cinematic bridge under heavy strain at dusk, vertical, no text"),
                ("Jatuh dari ketinggian yang biasa menjadi lebih keras. Atmosfer juga bisa lebih rapat jika gas tertarik lebih kuat, tetapi seberapa tebal udaranya butuh model yang tidak selesai dalam satu menit. Video ini tidak mengarang tekanan barometer.", "Debu jatuh cepat di seberkas cahaya.", "cinematic dust falling fast through a shaft of light, vertical, no text"),
                ("Gravitasi tidak berlipat pagi ini. Cerita ini hanya membuat beban yang biasa kamu anggap ringan terasa terlihat. Menurutmu, gedung atau tubuh yang lebih dulu kewalahan?", "Kaki di atas tanah yang retak halus.", "cinematic feet on cracked ground, cinematic light, vertical, no text"),
            ],
            "penjelasan": "Berat adalah gaya, massa tidak berubah hanya karena gravitasi permukaan berubah. Struktur dan tulang dirancang untuk gravitasi yang sekarang kita alami.",
            "batas": "Menggandakan gravitasi Bumi tanpa mengubah massa planet tidak konsisten dengan hukum gravitasi yang dikenal. Dampak medis rincinya tidak dihitung.",
            "ending": "Gravitasi tidak berlipat pagi ini. Beban yang biasa kita abaikan jadi terlihat dalam skenario ini.",
            "tanya": "Menurutmu, gedung atau tubuh yang lebih dulu kewalahan?",
            "judul": "Bagaimana jika gravitasi menjadi dua kali lebih kuat?",
            "deskripsi": "Skenario fiksi tentang berat, bangunan, dan jatuh jika gravitasi permukaan berlipat dua. Bukan model teknik.",
            "tag": ["gravitasi", "fisika", "what if", "bumi", "shorts"],
            "sumber": ["Berat bergantung pada gravitasi permukaan adalah pengetahuan fisika dasar."],
        },
        {
            "topik": "Kecepatan cahaya menjadi setengahnya",
            "inti": "cahaya setengah",
            "judul_kerja": "Jika cahaya melambat setengah",
            "hook": "Bagaimana jika kecepatan cahaya menjadi setengahnya, bukan hanya lampu di kamarmu yang redup?",
            "adegan": [
                ("Bagaimana jika cahaya melambat setengah?", "Kilat yang merambat terlalu pelan di awan.", "cinematic slow lightning across storm clouds, vertical, no text"),
                ("Cahaya adalah batas informasi dalam fisika yang kita pakai. Mengubah kecepatannya tidak sama dengan menurunkan saklar. Reaksi kimia, ukuran atom, dan cara matahari menghasilkan energi ikut bergantung pada tetapan yang sama.", "Matahari yang tampak asing di atas laut.", "cinematic alien looking sun over the ocean, vertical, no text"),
                ("Karena itu, skenario ini cepat meninggalkan kehidupan seperti yang kita kenal. Tidak ada jawaban tunggal tentang apakah manusia sempat menyadarinya. Yang jujur dikatakan: alam semesta dengan tetapan lain bukan sekadar dunia yang lebih lambat.", "Laboratorium dengan cahaya yang terpecah.", "cinematic prism splitting light in a dark lab, vertical, no text"),
                ("Kecepatan cahaya tidak sedang berubah. Pertanyaannya berguna karena menunjukkan betapa banyak hal yang diam-diam bergantung padanya. Bagian mana yang paling sulit kamu bayangkan?", "Sinar tipis di ruang gelap.", "cinematic single beam of light in a dark room, vertical, no text"),
            ],
            "penjelasan": "Kecepatan cahaya di ruang hampa adalah tetapan dasar dalam fisika modern. Ia masuk ke hubungan massa dan energi serta ke struktur elektromagnetik yang menopang kimia.",
            "batas": "Tidak ada cara yang diketahui untuk menjadikan kecepatan cahaya setengahnya hanya di Bumi. Video ini tidak menyajikan akibat numerik seolah-olah sudah diukur.",
            "ending": "Kecepatan cahaya tidak sedang berubah. Banyak hal yang biasa kita pakai diam-diam bergantung padanya.",
            "tanya": "Bagian mana dari skenario ini yang paling sulit kamu bayangkan?",
            "judul": "Bagaimana jika kecepatan cahaya menjadi setengah?",
            "deskripsi": "Skenario fiksi tentang tetapan fisika jika cahaya jauh lebih lambat. Bukan eksperimen yang bisa dilakukan.",
            "tag": ["kecepatan cahaya", "fisika", "what if", "sains", "shorts"],
            "sumber": ["Kecepatan cahaya sebagai tetapan dasar adalah pengetahuan fisika modern."],
        },
    ],
    "Teknologi dan AI": [
        {
            "topik": "AI mengatur semua lampu lalu lintas",
            "inti": "ai lampu lalu lintas",
            "judul_kerja": "Jika AI mengatur semua lampu",
            "hook": "Bagaimana jika kecerdasan buatan mengatur semua lampu lalu lintas di dunia, mulai dari perempatan di depan rumahmu?",
            "adegan": [
                ("Bagaimana jika AI mengatur semua lampu?", "Perempatan kota saat senja, lampu berganti.", "cinematic city intersection at dusk with traffic lights, vertical, no text"),
                ("Di cerita ini, sistem mencoba memendekkan antrean dengan membaca sensor. Sebagian jalan bisa lebih lancar. Sebagian lain menunggu lebih lama karena tujuan sistem bukan keadilan yang kamu rasakan di satu mobil.", "Antrean mobil yang tidak sama panjangnya.", "cinematic uneven traffic queues at a junction, vertical, no text"),
                ("Kalau sensor salah atau jaringan putus, kota tidak boleh gelap total. Lampu butuh mode cadangan yang sederhana, dan tanggung jawabnya tetap di manusia yang memasangnya. Video ini tidak mengklaim kecelakaan turun sekian persen.", "Ruang kendali dengan peta kota.", "cinematic traffic control room with a city map, no readable text, vertical"),
                ("Belum ada satu AI yang memegang semua lampu dunia. Menurutmu, kamu mau antrean yang rata, atau jalan utama yang selalu hijau?", "Lampu kuning tercermin di aspal basah.", "cinematic yellow traffic light reflected on wet asphalt, vertical, no text"),
            ],
            "penjelasan": "Lampu lalu lintas adaptif sudah diuji di beberapa kota dengan sensor dan algoritma, tetapi skalanya lokal. Sistem otomatis tetap butuh batas aman saat data hilang.",
            "batas": "Tidak ada sistem tunggal yang mengatur seluruh lampu dunia. Video ini tidak memberi angka penurunan kecelakaan atau waktu tempuh.",
            "ending": "Belum ada satu AI yang memegang semua lampu dunia. Mode cadangan tetap harus ada di tangan manusia.",
            "tanya": "Kamu mau antrean yang rata, atau jalan utama yang selalu hijau?",
            "judul": "Bagaimana jika AI mengatur semua lampu lalu lintas?",
            "deskripsi": "Skenario fiksi tentang lampu adaptif jika satu sistem mengatur semua perempatan. Bukan laporan kota nyata.",
            "tag": ["ai", "lalu lintas", "what if", "teknologi", "shorts"],
            "sumber": ["Lampu lalu lintas adaptif berbasis sensor sudah ada di sebagian kota, bukan satu otak global."],
        },
        {
            "topik": "Internet mati di seluruh dunia sehari",
            "inti": "internet mati sehari",
            "judul_kerja": "Jika internet mati sehari",
            "hook": "Bagaimana jika internet mati di seluruh dunia selama satu hari, sementara listrik di rumahmu tetap menyala?",
            "adegan": [
                ("Bagaimana jika internet mati sehari?", "Ponsel yang layarnya berputar tanpa jaringan.", "cinematic phone with a blank loading screen in a cafe, no readable text, vertical"),
                ("Pembayaran, peta, dan pesan yang biasa lewat pusat data ikut berhenti. Radio, percakapan langsung, dan sebagian mesin yang tidak bergantung pada jaringan masih bisa jalan. Mati internet tidak sama dengan mati listrik.", "Kasir dan uang kertas di meja.", "cinematic cashier counter with paper bills, vertical, no text"),
                ("Rumah sakit dan bandara yang punya prosedur darurat tidak serta-merta tutup, tetapi koordinasi yang biasa lewat jaringan menjadi lambat. Sehari terlalu pendek untuk meruntuhkan peradaban, dan terlalu panjang untuk dianggap sepele.", "Lorong rumah sakit yang tetap terang.", "cinematic hospital corridor with warm practical light, vertical, no text"),
                ("Internet tidak dijadwalkan mati besok. Cerita ini hanya menandai pekerjaan mana yang diam-diam numpang jaringan. Pekerjaanmu yang mana yang tetap jalan tanpa sinyal?", "Kabel di bawah jalan yang gelap.", "cinematic underground cable tunnel, cinematic light, vertical, no text"),
            ],
            "penjelasan": "Banyak layanan harian menumpang koneksi data, tetapi listrik, radio, dan perawatan darurat tidak identik dengan internet. Ketergantungan tiap kota berbeda.",
            "batas": "Video ini tidak meramalkan kekacauan total dalam 24 jam dan tidak menyebut jumlah kerugian uang.",
            "ending": "Internet tidak dijadwalkan mati besok. Sehari cukup untuk melihat apa yang diam-diam numpang jaringan.",
            "tanya": "Pekerjaanmu yang mana yang tetap jalan tanpa sinyal?",
            "judul": "Bagaimana jika internet mati sehari?",
            "deskripsi": "Skenario fiksi tentang layanan harian jika internet global berhenti satu hari, sementara listrik tetap ada.",
            "tag": ["internet", "teknologi", "what if", "kota", "shorts"],
            "sumber": ["Ketergantungan layanan digital pada jaringan adalah pengamatan umum, tanpa angka kerugian di video ini."],
        },
    ],
    "Masa Depan Peradaban": [
        {
            "topik": "Semua satelit mati bersamaan",
            "inti": "satelit mati",
            "judul_kerja": "Jika semua satelit mati",
            "hook": "Bagaimana jika semua satelit mati bersamaan pagi ini? Peta di saku bukan satu-satunya yang kehilangan patokan.",
            "adegan": [
                ("Bagaimana jika semua satelit mati?", "Langit subuh tanpa jejak satelit.", "cinematic dawn sky without satellite streaks, vertical, no text"),
                ("Navigasi satelit yang biasa memandu kapal, pesawat, dan pengiriman barang menjadi gelap. Jam presisi yang menumpang sinyal yang sama juga bergeser. Sebagian sistem punya cadangan di darat, tetapi tidak semuanya siap dalam hitungan menit.", "Kapal di laut yang berkabut.", "cinematic cargo ship in foggy sea, vertical, no text"),
                ("Cuaca tetap bisa diamati dari darat, hanya lebih jarang untuk wilayah yang biasa mengandalkan citra satelit. Cerita ini tidak mematikan Matahari atau gravitasi. Yang hilang adalah mata dan jam yang kita taruh di orbit.", "Stasiun cuaca di bukit.", "cinematic hilltop weather station at sunrise, vertical, no text"),
                ("Satelit tidak mati serentak hari ini. Menurutmu, hilangnya peta, ramalan cuaca, atau jam yang tepat yang paling mengganggu harimu?", "Ruang kendali satelit yang gelap.", "cinematic dark satellite control room, screens off, no readable text, vertical"),
            ],
            "penjelasan": "Navigasi satelit dipakai transportasi dan juga sebagai acuan waktu. Pengamatan cuaca modern menggabungkan satelit dan alat di darat. Keduanya tidak sama pentingnya di setiap negara.",
            "batas": "Tidak ada skenario operasional yang mematikan seluruh satelit dalam satu menit. Video ini tidak menyebut jumlah kecelakaan.",
            "ending": "Satelit tidak mati serentak hari ini. Yang terasa hilang adalah mata dan jam yang kita taruh di orbit.",
            "tanya": "Hilangnya peta, cuaca, atau jam yang tepat yang paling mengganggu harimu?",
            "judul": "Bagaimana jika semua satelit mati bersamaan?",
            "deskripsi": "Skenario fiksi tentang navigasi, waktu, dan cuaca jika satelit berhenti serentak. Bukan berita keadaan darurat.",
            "tag": ["satelit", "navigasi", "what if", "masa depan", "shorts"],
            "sumber": ["Navigasi satelit juga dipakai sebagai acuan waktu adalah pengetahuan teknologi yang sudah luas."],
        },
        {
            "topik": "Kota tanpa sampah selama sebulan",
            "inti": "kota tanpa sampah",
            "judul_kerja": "Jika kota tanpa sampah",
            "hook": "Bagaimana jika kotamu tidak menghasilkan sampah sama sekali selama sebulan? Bukan kota yang tiba-tiba menjadi bersih dengan sihir.",
            "adegan": [
                ("Bagaimana jika kota tanpa sampah?", "Gang kota yang biasa penuh kantong, kini kosong.", "cinematic clean narrow city alley at morning, vertical, no text"),
                ("Supaya sampah nol, barang yang masuk kota harus berubah: kemasan, sisa makanan, dan barang rusak butuh tempat kembali. Truk sampah yang hilang dari cerita ini memindahkan pekerjaan ke dapur dan ke pabrik, bukan menghapusnya.", "Dapur dengan wadah yang bisa dipakai ulang.", "cinematic kitchen with reusable containers, vertical, no text"),
                ("Sebulan terlalu singkat untuk mengubah tambang dan pabrik dunia, tetapi cukup untuk melihat barang mana yang sebenarnya sekali pakai. Kota yang rapi di layar belum berarti jejak bahan bakunya hilang di tempat lain.", "Tumpukan bahan di gudang yang tertata.", "cinematic organized warehouse of raw materials, vertical, no text"),
                ("Tidak ada kota besar yang benar-benar nol sampah bulan ini. Kalau satu jenis sampah harus pergi lebih dulu, kamu pilih kemasan makanan atau pakaian?", "Tangan menutup toples kaca.", "cinematic hands closing a glass jar, warm light, vertical, no text"),
            ],
            "penjelasan": "Sampah kota adalah ujung dari barang yang diproduksi, dikemas, dan dibuang. Mengurangi di rumah tidak otomatis menghapus limbah di pabrik atau tambang.",
            "batas": "Video ini tidak mengklaim sebuah kota sudah mencapai nol sampah, dan tidak memberi persentase daur ulang sebagai fakta lokal.",
            "ending": "Tidak ada kota besar yang benar-benar nol sampah bulan ini. Pekerjaan sampah lebih sering pindah tempat daripada lenyap.",
            "tanya": "Kalau satu jenis sampah harus pergi lebih dulu, kamu pilih kemasan makanan atau pakaian?",
            "judul": "Bagaimana jika kota tanpa sampah sebulan?",
            "deskripsi": "Skenario fiksi tentang barang dan limbah jika sebuah kota mencoba nol sampah selama sebulan.",
            "tag": ["sampah", "kota", "what if", "masa depan", "shorts"],
            "sumber": ["Sampah rumah tangga hanya sebagian dari jejak bahan sebuah kota. Tidak ada angka lokal yang dikarang di sini."],
        },
    ],
}


def _dari_data(nama_kategori: str, data: dict, topik_paksa: str | None):
    from .script_gen import AdeganNaskah, Naskah, rapikan

    judul_layar = [
        "Bagaimana jika ini terjadi?",
        "Akibat pertama",
        "Yang berkembang",
        "Batas ceritanya",
    ]
    sfx = ["whoosh", "whoosh", "pop", "pop"]
    adegan = []
    for urut, (narasi, visual, gambar), layar, efek in zip(
        ("hook", "awal", "puncak", "penutup"), data["adegan"], judul_layar, sfx
    ):
        if urut == "hook" and len(narasi.split()) < 12:
            narasi = data["hook"]
        adegan.append(AdeganNaskah(
            id=urut,
            narasi=narasi,
            visual=visual,
            prompt_gambar=gambar,
            subtitle=narasi,
            judul_layar=layar,
            sfx=efek,
        ))
    topik = data["topik"]
    perlu = False
    if topik_paksa and topik_paksa.strip().lower() != topik.lower():
        topik = topik_paksa.strip()
        perlu = True
    return rapikan(Naskah(
        topik=topik,
        kategori=nama_kategori,
        inti=data["inti"],
        judul_kerja=data["judul_kerja"],
        hook=data["hook"],
        adegan=adegan,
        penjelasan_ilmiah=data["penjelasan"],
        batas_ketidakpastian=data["batas"] + (" Kerangka ini perlu ditinjau karena topiknya dipaksa." if perlu else ""),
        ending=data["ending"],
        pertanyaan_komentar=data["tanya"],
        judul_youtube=data["judul"],
        deskripsi_youtube=data["deskripsi"],
        hashtag=data["tag"],
        referensi=data["sumber"],
        pengungkapan_sintetis=True,
        perlu_tinjauan=perlu,
    ))


def template_lokal(kategori, kategori_besok, label_berikut, topik=None, hindari=()):
    del kategori_besok, label_berikut
    nama = kategori[0]
    varian = BANK.get(nama) or BANK["Fisika"]
    dipilih = varian[0]
    for calon in varian:
        if topik and topik.strip().lower() == calon["topik"].lower():
            dipilih = calon
            break
        if not topik and not mirip_dengan_daftar(calon["topik"], calon["inti"], list(hindari or [])):
            dipilih = calon
            break
    return _dari_data(nama if nama in BANK else "Fisika", dipilih, topik)


TOPIK = {nama: varian[0]["topik"] for nama, varian in BANK.items()}
TOPIK_CADANGAN = {nama: varian[-1]["topik"] for nama, varian in BANK.items()}
