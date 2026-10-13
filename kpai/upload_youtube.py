from pathlib import Path

from . import config

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRET = config.SECRETS_DIR / "client_secret.json"
TOKEN = config.SECRETS_DIR / "token.json"


def login(interaktif: bool = True):
    from google.auth.exceptions import RefreshError
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES) if TOKEN.exists() else None
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            TOKEN.write_text(creds.to_json(), encoding="utf-8")
            return creds
        except RefreshError:
            creds = None
    if not interaktif:
        raise SystemExit("Login YouTube kedaluwarsa. Jalankan sekali: .venv\\Scripts\\python main.py --login")
    if not CLIENT_SECRET.exists():
        raise SystemExit(f"File {CLIENT_SECRET} belum ada. Lihat bagian 'Upload YouTube' di README.md.")

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent")
    config.SECRETS_DIR.mkdir(exist_ok=True)
    TOKEN.write_text(creds.to_json(), encoding="utf-8")
    return creds


def upload(video: Path, judul: str, deskripsi: str, tags: list[str]) -> str:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    yt = build("youtube", "v3", credentials=login(interaktif=False))
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
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    return resp["id"]
