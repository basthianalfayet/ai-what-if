"""Keputusan provider. FREE_ONLY benar-benar menutup jalur berbayar."""

from datetime import datetime, timedelta

from . import config


def mode() -> str:
    if config.PROVIDER_MODE in ("free_safe", "auto_fallback", "local_only"):
        return config.PROVIDER_MODE
    return "free_safe"


def lokal() -> bool:
    return mode() == "local_only"


def platform_aktif(nama: str) -> bool:
    if nama == "telegram":
        return config.TELEGRAM_ENABLED
    if nama == "youtube":
        return config.PLATFORM_MODE == "youtube_only"
    return False


def boleh_berbayar() -> bool:
    if config.FREE_ONLY or not config.PAID_FALLBACK_ENABLED:
        return False
    return mode() == "auto_fallback"


def boleh_naskah_api() -> bool:
    return not lokal()


def boleh_gambar_api() -> bool:
    return not lokal() and config.IMAGE_PROVIDER == "cloudflare"


def boleh_horde() -> bool:
    """Hanya mode auto dan hanya kalau HORDE_ENABLED dinyalakan eksplisit."""
    if lokal() or mode() != "auto_fallback" or not config.HORDE_ENABLED:
        return False
    return config.IMAGE_FALLBACK_PROVIDER in ("horde", "local_assets", "")


def boleh_suara_api() -> bool:
    return not lokal() and config.TTS_PROVIDER == "edge_tts"


def fallback_naskah_lokal() -> bool:
    if lokal():
        return False
    return config.SCRIPT_LOCAL_FALLBACK and config.TEXT_FALLBACK_ENABLED


def _baca_json(path, kosong):
    if not path.exists():
        return kosong
    try:
        import json
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return kosong


def _tulis_json(path, data) -> None:
    import json
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _saat(mentah: str) -> datetime | None:
    try:
        saat = datetime.fromisoformat(mentah)
    except ValueError:
        return None
    if saat.tzinfo is None:
        saat = saat.replace(tzinfo=config.WIB)
    return saat


def dalam_cooldown(nama: str) -> bool:
    data = _baca_json(config.COOLDOWN_FILE, {"provider": {}})
    mentah = (data.get("provider") or {}).get(nama.lower())
    if not mentah:
        return False
    saat = _saat(str(mentah))
    return bool(saat and config.sekarang_wib() < saat)


def catat_cooldown(nama: str, jam: float) -> None:
    data = _baca_json(config.COOLDOWN_FILE, {"provider": {}})
    provider = data.setdefault("provider", {})
    sampai = config.sekarang_wib() + timedelta(hours=jam)
    provider[nama.lower()] = sampai.isoformat()
    _tulis_json(config.COOLDOWN_FILE, data)


def cooldown_kuota(nama: str) -> None:
    """Kuota harian tidak dicoba lagi sampai lewat tengah malam WIB."""
    sekarang = config.sekarang_wib()
    besok = (sekarang + timedelta(days=1)).replace(hour=0, minute=10, second=0, microsecond=0)
    jam = max((besok - sekarang).total_seconds() / 3600, 0.5)
    catat_cooldown(nama, jam)


def sisa_gambar() -> int:
    data = _baca_json(config.KUOTA_FILE, {"hari": {}})
    terpakai = int((data.get("hari") or {}).get(config.sekarang_wib().date().isoformat(), 0))
    return max(0, config.IMAGE_DAILY_MAX - terpakai)


def catat_gambar(jumlah: int) -> None:
    if jumlah <= 0:
        return
    data = _baca_json(config.KUOTA_FILE, {"hari": {}})
    hari = data.setdefault("hari", {})
    kunci = config.sekarang_wib().date().isoformat()
    hari[kunci] = int(hari.get(kunci, 0)) + jumlah
    if len(hari) > 21:
        for lama in sorted(hari)[:-14]:
            hari.pop(lama, None)
    _tulis_json(config.KUOTA_FILE, data)
