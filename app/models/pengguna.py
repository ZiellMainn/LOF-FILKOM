"""Entity Pengguna (abstrak) dan turunannya sesuai class diagram."""
from abc import ABC, abstractmethod

ROLE_CIVITAS = "Civitas Akademika"
ROLE_STAF = "Staf Kemahasiswaan"
ROLE_PIMPINAN = "Pimpinan Kemahasiswaan"


class Pengguna(ABC):
    role = ""

    def __init__(self, row):
        data = dict(row)
        self.id_user = data["id_user"]
        self.nama = data["nama"]
        self.nim_nip = data["nim_nip"]
        self.email = data["email"]
        self.no_telp = data.get("no_telp")

    @abstractmethod
    def hak_akses(self) -> frozenset:
        """Daftar izin yang dimiliki peran ini."""

    def boleh(self, izin: str) -> bool:
        return izin in self.hak_akses()

    @property
    def inisial(self) -> str:
        bagian = [b for b in self.nama.split() if b]
        return "".join(b[0] for b in bagian[:2]).upper() or "?"

    @staticmethod
    def dari_row(row):
        peta = {c.role: c for c in (CivitasAkademika, StafKemahasiswaan, PimpinanKemahasiswaan)}
        return peta[row["role"]](row)


class CivitasAkademika(Pengguna):
    role = ROLE_CIVITAS

    def hak_akses(self):
        return frozenset({"lapor", "cari", "status"})


class StafKemahasiswaan(Pengguna):
    role = ROLE_STAF

    def hak_akses(self):
        return frozenset({"lapor", "cari", "status", "verifikasi", "lihat_detail"})


class PimpinanKemahasiswaan(Pengguna):
    role = ROLE_PIMPINAN

    def hak_akses(self):
        return frozenset({"cari", "rekap", "lihat_detail"})
