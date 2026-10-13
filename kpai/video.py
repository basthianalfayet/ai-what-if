import math
import random
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from . import config
from .render import H, W
from .tts import Kata, buat_suara

JEDA = 0.35
JEDA_AKHIR = 1.4
FPS = 30

_SFX = {
    "whoosh": "anoisesrc=d=0.5:c=pink:r=48000:a=0.8,highpass=f=300,lowpass=f=4000,"
              "afade=t=in:st=0:d=0.22,afade=t=out:st=0.22:d=0.28",
    "pop": "sine=f=900:d=0.09:r=48000,afade=t=out:st=0:d=0.09",
}
_VOLUME_SFX = {"whoosh": 0.45, "pop": 0.35}


@dataclass
class Adegan:
    nama: str
    audio: Path
    kata: list[Kata]
    durasi: float
    mulai: float = 0.0
    jeda: float = JEDA

    @property
    def panjang(self) -> float:
        return self.durasi + self.jeda


def buat_suara_adegan(naskah, folder: Path) -> list[Adegan]:
    teks = [
        ("hook", naskah.hook),
        ("prompt", naskah.narasi_prompt),
        ("hasil", naskah.narasi_hasil),
        ("trik", naskah.narasi_trik),
        ("penutup", naskah.penutup),
    ]
    adegan, t = [], 0.0
    for nama, isi in teks:
        path = folder / f"suara_{nama}.mp3"
        kata, durasi = buat_suara(isi, path)
        a = Adegan(nama, path, kata, durasi, mulai=t, jeda=JEDA_AKHIR if nama == "penutup" else JEDA)
        adegan.append(a)
        t += a.panjang
        print(f"  Suara {nama}: {durasi:.1f} detik")
    return adegan


def _siapkan_sfx(folder: Path) -> dict[str, Path]:
    hasil = {}
    for nama, sumber in _SFX.items():
        path = folder / f"sfx_{nama}.wav"
        subprocess.run(
            [config.ffmpeg(), "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", sumber, "-ac", "2", str(path)],
            check=True,
        )
        hasil[nama] = path
    return hasil


def _pilih_musik() -> Path | None:
    if not config.MUSIC_DIR.exists():
        return None
    lagu = [p for p in config.MUSIC_DIR.iterdir() if p.suffix.lower() in (".mp3", ".wav", ".m4a", ".ogg")]
    return random.choice(lagu) if lagu else None


def _filter_audio(adegan, transisi, idx_sfx, idx_musik, total) -> str:
    bagian, label = [], []
    for i, a in enumerate(adegan, start=1):
        bagian.append(
            f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,apad=pad_dur={a.jeda:.3f},"
            f"atrim=0:{a.panjang:.3f}[a{i}]"
        )
        label.append(f"[a{i}]")
    bagian.append(f"{''.join(label)}concat=n={len(adegan)}:v=0:a=1[suara]")
    campur = ["[suara]"]

    for jenis, idx in idx_sfx.items():
        waktu = [t for t, j in transisi if j == jenis]
        if not waktu:
            continue
        salinan = "".join(f"[{jenis}{k}]" for k in range(len(waktu)))
        bagian.append(f"[{idx}:a]volume={_VOLUME_SFX[jenis]},asplit={len(waktu)}{salinan}")
        for k, t in enumerate(waktu):
            mundur = max(0, int(t * 1000) - (120 if jenis == "whoosh" else 0))
            bagian.append(f"[{jenis}{k}]adelay={mundur}:all=1[{jenis}d{k}]")
            campur.append(f"[{jenis}d{k}]")

    if idx_musik is not None:
        bagian.append(
            f"[{idx_musik}:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.10,"
            f"afade=t=out:st={max(total - 1.5, 0):.3f}:d=1.5[musik]"
        )
        campur.append("[musik]")

    bagian.append(f"{''.join(campur)}amix=inputs={len(campur)}:duration=first:dropout_transition=0:normalize=0[audio]")
    return ";".join(bagian)


def render_video(renderer, adegan: list[Adegan], folder: Path, keluaran: Path) -> float:
    total = renderer.total
    sfx = _siapkan_sfx(folder)
    musik = _pilih_musik()

    cmd = [config.ffmpeg(), "-y", "-hide_banner", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    for a in adegan:
        cmd += ["-i", str(a.audio)]
    idx_sfx = {}
    for nama, path in sfx.items():
        idx_sfx[nama] = len(adegan) + 1 + len(idx_sfx)
        cmd += ["-i", str(path)]
    idx_musik = None
    if musik:
        idx_musik = len(adegan) + 1 + len(idx_sfx)
        cmd += ["-stream_loop", "-1", "-i", str(musik)]
        print(f"  Musik: {musik.name}")

    cmd += [
        "-filter_complex", _filter_audio(adegan, renderer.transisi, idx_sfx, idx_musik, total),
        "-map", "0:v", "-map", "[audio]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k",
        "-t", f"{total:.3f}", "-movflags", "+faststart",
        str(keluaran),
    ]

    jumlah = math.ceil(total * FPS)
    mulai = time.time()
    proses = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for i in range(jumlah):
            proses.stdin.write(renderer.frame(i / FPS).tobytes())
            if i and i % (FPS * 10) == 0:
                print(f"  {i}/{jumlah} frame ({time.time() - mulai:.0f} detik)")
    finally:
        proses.stdin.close()
        kode = proses.wait()
    if kode != 0:
        raise RuntimeError(f"FFmpeg gagal (kode {kode})")
    for p in sfx.values():
        p.unlink(missing_ok=True)
    print(f"  {jumlah} frame dirender dalam {time.time() - mulai:.0f} detik")
    return total
