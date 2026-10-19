"""Kunci slot supaya dua proses tidak membuat video yang sama."""

import os
import time
from pathlib import Path

from . import config


class SlotTerkunci(RuntimeError):
    pass


class KunciSlot:
    def __init__(self, nama: str):
        self.path = Path(config.LOCK_DIR) / f"{nama}.lock"
        self.fd = None

    def _basi(self) -> bool:
        try:
            return time.time() - self.path.stat().st_mtime > config.LOCK_DETIK
        except OSError:
            return True

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        for _ in range(2):
            try:
                self.fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(self.fd, f"{os.getpid()} {time.time():.0f}\n".encode())
                return self
            except FileExistsError:
                if self._basi():
                    self.path.unlink(missing_ok=True)
                    continue
                raise SlotTerkunci(f"Slot {self.path.stem} sedang diproses proses lain.") from None
        raise SlotTerkunci(f"Slot {self.path.stem} sedang diproses proses lain.")

    def __exit__(self, *_args):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        self.path.unlink(missing_ok=True)
        return False
