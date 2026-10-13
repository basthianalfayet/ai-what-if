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


def sudah_dibuat(data: dict, tgl: date, slot: str) -> bool:
    return any(v["tanggal"] == tgl.isoformat() and v.get("slot", "pagi") == slot for v in data["video"])


def topik_lama(data: dict) -> list[str]:
    return [v["topik"] for v in data["video"]]


def minggu_ini(data: dict, tgl: date) -> list[str]:
    senin = tgl - timedelta(days=tgl.weekday())
    return [v["judul"] for v in data["video"] if senin.isoformat() <= v["tanggal"] <= tgl.isoformat()]
