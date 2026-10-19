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
