"""Catatan upload persisten. Video yang sama tidak diunggah dua kali."""

import hashlib
import json
from pathlib import Path

from . import config


def _muat() -> dict:
    if config.LEDGER_FILE.exists():
        try:
            data = json.loads(config.LEDGER_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
    else:
        data = {}
    data.setdefault("unggahan", [])
    return data


def simpan(data: dict) -> None:
    config.LEDGER_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.LEDGER_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def kunci_berkas(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as berkas:
        while True:
            potong = berkas.read(1024 * 1024)
            if not potong:
                break
            hasher.update(potong)
    return hasher.hexdigest()


def cari(data: dict, kunci: str) -> dict | None:
    for item in data["unggahan"]:
        if item.get("kunci") == kunci or item.get("id_video") == kunci:
            return item
    return None


def boleh_ulang(status: str | None) -> bool:
    return status in (None, "gagal", "gagal_oauth", "gagal_kuota")


def catat(data: dict, entri: dict) -> None:
    lama = cari(data, entri["kunci"])
    if lama:
        lama.update(entri)
        return
    data["unggahan"].append(entri)
