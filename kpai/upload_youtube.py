from pathlib import Path

from . import config
from .kualitas import unggah_diizinkan
from .ledger import _muat, boleh_ulang, cari, catat, kunci_berkas, simpan as simpan_ledger

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]
CLIENT_SECRET = config.YT_DIR / "client_secret.json"
TOKEN = config.YT_DIR / "token.json"
TOKEN_LAMA = config.SECRETS_DIR / "token.json"


def kanal_sesuai(judul: str, diharapkan: str) -> bool:
    return (judul or "").casefold().strip() == (diharapkan or "").casefold().strip()


def login(interaktif: bool = True):
    from google.auth.exceptions import RefreshError
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    if TOKEN_LAMA.exists() and not TOKEN.exists():
        print("Token lama di secrets/token.json diabaikan. Login kanal baru menyimpan token di secrets/youtube_whatif/token.json.")
    creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES) if TOKEN.exists() else None
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            TOKEN.parent.mkdir(parents=True, exist_ok=True)
            TOKEN.write_text(creds.to_json(), encoding="utf-8")
            return creds
        except RefreshError:
            creds = None
    if not interaktif:
        raise SystemExit("Login YouTube kedaluwarsa. Jalankan sekali: .venv\\Scripts\\python main.py --login")
    if not CLIENT_SECRET.exists():
        raise SystemExit(f"File {CLIENT_SECRET} belum ada. Lihat bagian autentikasi YouTube di README.md.")

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent")
    TOKEN.parent.mkdir(parents=True, exist_ok=True)
    TOKEN.write_text(creds.to_json(), encoding="utf-8")
    return creds


def _judul_kanal(creds) -> str:
    from googleapiclient.discovery import build

    yt = build("youtube", "v3", credentials=creds)
    resp = yt.channels().list(part="snippet", mine=True).execute()
    item = (resp.get("items") or [None])[0]
    if not item:
        raise SystemExit("Token ini tidak terhubung ke channel YouTube. Upload dibatalkan.")
    return item["snippet"]["title"]


def upload(video: Path, judul: str, deskripsi: str, tags: list[str], id_video: str = "") -> str:
    if not unggah_diizinkan(
        uji=config.MODE_UJI,
        dry_run=config.DRY_RUN,
        yt_upload=config.YT_UPLOAD,
        kualitas_lolos=True,
        sudah_unggah=False,
        platform="youtube",
    ):
        raise SystemExit("Upload tidak dijalankan. Mode uji, dry-run, atau YT_UPLOAD=0.")
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    data = _muat()
    kunci = kunci_berkas(video)
    ada = cari(data, kunci) or (cari(data, id_video) if id_video else None)
    if ada and not boleh_ulang(ada.get("status")):
        if ada.get("status") == "berhasil" and ada.get("video_id"):
            print(f"  Upload dilewati, video ini sudah tercatat: {ada['video_id']}")
            return ada["video_id"]
        raise SystemExit("Status upload tidak pasti. Tidak diulang sebelum diperiksa manual di YouTube Studio.")

    creds = login(interaktif=False)
    judul_kanal = _judul_kanal(creds)
    if not kanal_sesuai(judul_kanal, config.YT_CHANNEL_NAME):
        raise SystemExit(
            f"Kanal YouTube '{judul_kanal}' bukan '{config.YT_CHANNEL_NAME}'. "
            "Upload dibatalkan supaya token lama tidak salah sasaran."
        )
    yt = build("youtube", "v3", credentials=creds)
    body = {
        "snippet": {
            "title": judul[:100],
            "description": deskripsi[:4900],
            "tags": tags,
            "categoryId": "27",
            "defaultLanguage": "id",
            "defaultAudioLanguage": "id",
        },
        "status": {
            "privacyStatus": config.YT_PRIVACY,
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": True,
        },
    }
    media = MediaFileUpload(str(video), mimetype="video/mp4", chunksize=-1, resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    try:
        resp = None
        while resp is None:
            _, resp = req.next_chunk()
    except SystemExit:
        raise
    except Exception as e:
        from .errors import Jenis, klasifikasi_exception
        salah = klasifikasi_exception("YouTube", e)
        status = "gagal_oauth" if salah.jenis == Jenis.INVALID_KEY else "tidak_pasti"
        if salah.jenis == Jenis.QUOTA:
            status = "gagal_kuota"
        catat(data, {"kunci": kunci, "id_video": id_video, "status": status, "video_id": ""})
        simpan_ledger(data)
        raise
    video_id = resp["id"]
    catat(data, {
        "kunci": kunci,
        "id_video": id_video,
        "status": "berhasil",
        "video_id": video_id,
        "url": f"https://youtube.com/shorts/{video_id}",
    })
    simpan_ledger(data)
    return video_id
