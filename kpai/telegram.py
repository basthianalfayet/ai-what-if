from pathlib import Path

import requests

from . import config


def aktif() -> bool:
    return bool(config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID)


def _minta(metode: str, **kwargs) -> dict:
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/{metode}"
    try:
        r = requests.post(url, **kwargs)
        data = r.json()
    except (requests.RequestException, ValueError) as e:
        # Token ada di URL; jangan sampai ikut tercetak di log.
        raise RuntimeError(f"Telegram {metode} gagal: {str(e).replace(config.TELEGRAM_BOT_TOKEN, '<token>')}") from None
    if not data.get("ok"):
        raise RuntimeError(f"Telegram {metode} ditolak: {data.get('description')}")
    return data


def kirim_pesan(teks: str) -> None:
    if not aktif():
        return
    for awal in range(0, len(teks), 4000):
        _minta(
            "sendMessage",
            data={"chat_id": config.TELEGRAM_CHAT_ID, "text": teks[awal:awal + 4000], "disable_web_page_preview": True},
            timeout=60,
        )


def kirim_video(path: Path, caption: str, durasi: float) -> None:
    if not aktif():
        return
    with open(path, "rb") as f:
        _minta(
            "sendVideo",
            data={
                "chat_id": config.TELEGRAM_CHAT_ID,
                "caption": caption[:1024],
                "supports_streaming": True,
                "width": 1080,
                "height": 1920,
                "duration": int(durasi),
            },
            files={"video": (path.name, f, "video/mp4")},
            timeout=600,
        )


def cari_chat_id() -> None:
    if not config.TELEGRAM_BOT_TOKEN:
        raise SystemExit("Isi TELEGRAM_BOT_TOKEN di .env dulu.")
    try:
        data = _minta("getUpdates", timeout=30)
    except RuntimeError as e:
        raise SystemExit(str(e)) from None
    chat = {}
    for u in data.get("result", []):
        pesan = u.get("message") or u.get("channel_post") or {}
        c = pesan.get("chat")
        if c:
            chat[c["id"]] = c.get("username") or c.get("title") or c.get("first_name")
    if not chat:
        print("Belum ada pesan masuk ke bot. Buka bot kamu di Telegram, tekan Start, kirim 'halo', lalu jalankan perintah ini lagi.")
    for cid, nama in chat.items():
        print(f"TELEGRAM_CHAT_ID={cid}   ({nama})")
