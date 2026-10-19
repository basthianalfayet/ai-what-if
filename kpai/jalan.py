"""Menjalankan beberapa slot. Kegagalan satu slot tidak menghentikan yang lain."""


def jalankan_berurutan(langkah, fungsi) -> list[dict]:
    hasil = []
    for item in langkah:
        try:
            status = fungsi(item)
            hasil.append({"item": item, "status": status})
        except Exception as e:
            hasil.append({"item": item, "status": "gagal", "alasan": f"{type(e).__name__}: {e}"})
    return hasil
