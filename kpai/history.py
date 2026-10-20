import json
from datetime import date, timedelta

from . import config


def muat() -> dict:
    if config.HISTORY_FILE.exists():
        return json.loads(config.HISTORY_FILE.read_text(encoding="utf-8"))
    return {"video": [], "rencana": {}}


def simpan(data: dict) -> None:
    config.HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.HISTORY_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def kunci(tgl: date, slot: str) -> str:
    return f"{tgl.isoformat()}-{slot}"


def _kunci_video(video: dict) -> tuple[str, str]:
    return video["tanggal"], video.get("slot", "pagi")


_STATUS_SELESAI = {"selesai", "review", "terunggah"}


def sudah_dibuat(data: dict, tgl: date, slot: str) -> bool:
    for video in data["video"]:
        if _kunci_video(video) != (tgl.isoformat(), slot):
            continue
        status = video.get("status", "selesai")
        if status in _STATUS_SELESAI:
            return True
    return False


def jumlah_hari(data: dict, tgl: date) -> int:
    kunci = tgl.isoformat()
    return sum(
        1
        for video in data["video"]
        if video.get("tanggal") == kunci and video.get("status", "selesai") in _STATUS_SELESAI
    )


def boleh_slot_baru(data: dict, tgl: date, slot: str, paksa: bool = False) -> tuple[bool, str]:
    if paksa:
        return True, ""
    if sudah_dibuat(data, tgl, slot):
        return False, "slot sudah dibuat"
    if jumlah_hari(data, tgl) >= config.MAX_VIDEO_HARIAN:
        return False, "batas harian"
    return True, ""


def catat(data: dict, entri: dict) -> None:
    """Satu baris per tanggal+slot. Entri baru mengganti yang lama."""
    terakhir = {}
    for video in data["video"]:
        terakhir[_kunci_video(video)] = video
    terakhir[_kunci_video(entri)] = entri
    data["video"] = list(terakhir.values())


def seri_berjalan(data: dict) -> dict | None:
    """Seri yang belum selesai. Episode berikutnya memakai bagian[selesai]."""
    seri = data.get("seri") or {}
    bagian = [str(item).strip() for item in (seri.get("bagian") or []) if str(item).strip()]
    try:
        selesai = int(seri.get("selesai") or 0)
    except (TypeError, ValueError):
        selesai = 0
    if selesai < 0 or selesai >= 3 or len(bagian) < 3:
        return None
    return {
        "nama": str(seri.get("nama") or "").strip(),
        "kategori": str(seri.get("kategori") or "").strip(),
        "cakupan": str(seri.get("cakupan") or "").strip(),
        "selesai": selesai,
        "bagian": bagian[:3],
    }


def lanjutkan_seri(data: dict, naskah, kategori: str, cakupan: str, sedang: dict | None) -> None:
    if sedang:
        selesai = int(sedang["selesai"]) + 1
        if selesai >= 3:
            data["seri"] = {}
            return
        berikut = dict(sedang)
        berikut["selesai"] = selesai
        data["seri"] = berikut
        return
    bagian = [
        str(getattr(naskah, "judul_youtube", "") or getattr(naskah, "topik", "")).strip(),
        str(getattr(naskah, "topik_berikut", "")).strip(),
        str(getattr(naskah, "topik_ketiga", "")).strip(),
    ]
    if not all(bagian):
        return
    data["seri"] = {
        "nama": str(getattr(naskah, "judul_seri", "") or bagian[0]).strip(),
        "kategori": kategori,
        "cakupan": cakupan,
        "selesai": 1,
        "bagian": bagian,
    }


def topik_lama(data: dict) -> list[str]:
    hasil = []
    for video in data["video"]:
        if video.get("topik"):
            hasil.append(video["topik"])
        if video.get("inti"):
            hasil.append(video["inti"])
    return hasil


def minggu_ini(data: dict, tgl: date) -> list[str]:
    senin = tgl - timedelta(days=tgl.weekday())
    return [v["judul"] for v in data["video"] if senin.isoformat() <= v["tanggal"] <= tgl.isoformat()]
