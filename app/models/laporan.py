"""Entity Laporan (abstrak) dengan turunan LaporanKehilangan dan LaporanTemuan."""
from abc import ABC, abstractmethod

STATUS_LAPORAN = ("Dilaporkan", "Dicocokkan", "Diverifikasi", "Diambil")


class Laporan(ABC):
    def __init__(self, row):
        self.__dict__.update(dict(row))

    @abstractmethod
    def get_tipe(self) -> str:
        """Tipe laporan: Kehilangan atau Temuan."""

    @property
    def tipe_laporan(self):  # noqa: D401 - dipakai template
        return self.get_tipe()

    def milik(self, id_user: int) -> bool:
        return self.id_user == id_user

    @property
    def selesai(self) -> bool:
        return self.status == "Diambil"

    @property
    def tahap(self) -> int:
        """Indeks tahap status (0..3) untuk linimasa."""
        return STATUS_LAPORAN.index(self.status)

    @staticmethod
    def dari_row(row):
        return (LaporanKehilangan if row["tipe_laporan"] == "Kehilangan" else LaporanTemuan)(row)


class LaporanKehilangan(Laporan):
    def get_tipe(self):
        return "Kehilangan"


class LaporanTemuan(Laporan):
    def get_tipe(self):
        return "Temuan"
