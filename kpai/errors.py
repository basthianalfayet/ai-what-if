import re
from enum import Enum

from . import config


class Jenis(str, Enum):
    RATE_LIMIT = "rate_limit"
    QUOTA = "quota"
    TIMEOUT = "timeout"
    SERVER = "server"
    INVALID_KEY = "invalid_key"
    MODEL_UNAVAILABLE = "model_unavailable"
    BAD_IMAGE = "bad_image"
    PERMANENT = "permanent"


class ProviderError(Exception):
    def __init__(self, jenis: Jenis, provider: str, pesan: str, retry_after: float | None = None):
        self.jenis = jenis
        self.provider = provider
        self.pesan = pesan
        self.retry_after = retry_after
        super().__init__(f"{provider} {jenis.value}: {pesan}")


class NeedsReview(RuntimeError):
    def __init__(self, pesan: str, peringatan: list[str] | None = None, konfigurasi: list[str] | None = None):
        self.peringatan = peringatan or []
        self.konfigurasi = konfigurasi or []
        super().__init__(pesan)


def redaksi(teks: str) -> str:
    hasil = str(teks)
    for rahasia in (
        config.GEMINI_API_KEY,
        config.GROQ_API_KEY,
        config.CF_API_TOKEN,
        config.FAL_KEY,
        config.TELEGRAM_BOT_TOKEN,
    ):
        if rahasia and len(rahasia) > 4:
            hasil = hasil.replace(rahasia, "<redacted>")
    hasil = re.sub(r"Bearer\s+\S+", "Bearer <redacted>", hasil, flags=re.I)
    return hasil[:400]


def _kode(nilai) -> int:
    try:
        return int(nilai)
    except (TypeError, ValueError):
        return 0


def _header(headers, nama: str) -> str:
    if not headers:
        return ""
    if hasattr(headers, "get"):
        nilai = headers.get(nama) or headers.get(nama.lower()) or headers.get(nama.title())
        return str(nilai) if nilai else ""
    return ""


def retry_after(headers) -> float | None:
    nilai = _header(headers, "Retry-After")
    if not nilai:
        return None
    try:
        return max(0.0, float(nilai))
    except ValueError:
        return None


def _kuota(pesan: str) -> bool:
    teks = pesan.lower()
    kunci = (
        "quota",
        "kuota",
        "resource_exhausted",
        "daily free allocation",
        "insufficient_quota",
        "exceeded your current quota",
        "billing",
        "quota exceeded",
    )
    return any(k in teks for k in kunci)


def klasifikasi_http(provider: str, kode: int, pesan: str, headers=None) -> ProviderError:
    teks = redaksi(pesan)
    rendah = teks.lower()
    jeda = retry_after(headers)
    if _kuota(teks) and kode in (0, 400, 402, 403, 429):
        return ProviderError(Jenis.QUOTA, provider, teks)
    if kode == 401 or (kode == 403 and any(k in rendah for k in ("api key", "api_key", "unauthorized", "authentication"))):
        return ProviderError(Jenis.INVALID_KEY, provider, teks)
    if kode == 429 and _kuota(teks):
        return ProviderError(Jenis.QUOTA, provider, teks)
    if kode == 429:
        return ProviderError(Jenis.RATE_LIMIT, provider, teks, jeda)
    if kode in (408, 504):
        return ProviderError(Jenis.TIMEOUT, provider, teks)
    if 500 <= kode <= 599:
        return ProviderError(Jenis.SERVER, provider, teks)
    if kode == 404 or (kode == 0 and "model" in rendah and any(k in rendah for k in ("not found", "does not exist", "unknown model"))):
        return ProviderError(Jenis.MODEL_UNAVAILABLE, provider, teks)
    if kode == 0 and _kuota(teks):
        return ProviderError(Jenis.QUOTA, provider, teks)
    if kode == 0 and ("too many requests" in rendah or "rate limit" in rendah):
        return ProviderError(Jenis.RATE_LIMIT, provider, teks, jeda)
    if kode == 0 and ("timeout" in rendah or "timed out" in rendah):
        return ProviderError(Jenis.TIMEOUT, provider, teks)
    return ProviderError(Jenis.PERMANENT, provider, teks or f"HTTP {kode}")


def klasifikasi_exception(provider: str, exc: Exception) -> ProviderError:
    if isinstance(exc, ProviderError):
        return exc
    nama = exc.__class__.__name__.lower()
    if "timeout" in nama:
        return ProviderError(Jenis.TIMEOUT, provider, redaksi(exc))
    kode = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    headers = None
    resp = getattr(exc, "response", None)
    pesan = str(exc)
    if resp is not None:
        kode = kode or getattr(resp, "status_code", None)
        headers = getattr(resp, "headers", None)
        badan = getattr(resp, "text", None)
        if badan:
            pesan = f"{pesan} {badan}"
    return klasifikasi_http(provider, _kode(kode), pesan, headers)


def dari_response(provider: str, response) -> ProviderError | None:
    kode = _kode(getattr(response, "status_code", 0))
    if kode < 400:
        return None
    badan = getattr(response, "text", "") or ""
    return klasifikasi_http(provider, kode, badan[:500], getattr(response, "headers", None))
