import os
import uuid

from ..repositories.interfaces import IFotoStorage
from .errors import ValidasiError

# Tanda awal berkas (magic bytes) agar ekstensi tidak bisa dipalsukan.
_TANDA = {
    "jpg": (b"\xff\xd8\xff",),
    "jpeg": (b"\xff\xd8\xff",),
    "png": (b"\x89PNG\r\n\x1a\n",),
    "webp": (b"RIFF",),
}
MAKS_BYTE = 3 * 1024 * 1024


class FotoStorageLokal(IFotoStorage):
    def __init__(self, folder):
        self.folder = folder
        os.makedirs(folder, exist_ok=True)

    def simpan(self, berkas) -> str:
        """Menyimpan foto yang sudah valid dan mengembalikan nama berkas acak."""
        nama = (berkas.filename or "")
        ekstensi = nama.rsplit(".", 1)[-1].lower() if "." in nama else ""
        if ekstensi not in _TANDA:
            raise ValidasiError({"foto": "Format foto harus JPG, PNG, atau WEBP."})
        isi = berkas.read(MAKS_BYTE + 1)
        if len(isi) > MAKS_BYTE:
            raise ValidasiError({"foto": "Ukuran foto maksimal 3 MB."})
        if not any(isi.startswith(t) for t in _TANDA[ekstensi]) or (ekstensi == "webp" and isi[8:12] != b"WEBP"):
            raise ValidasiError({"foto": "Isi berkas bukan gambar yang valid."})
        nama_baru = f"{uuid.uuid4().hex}.{ekstensi}"
        with open(os.path.join(self.folder, nama_baru), "wb") as f:
            f.write(isi)
        return nama_baru
