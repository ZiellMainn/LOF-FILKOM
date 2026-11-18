"""Entity pendukung: Kategori, Lokasi, RiwayatStatus, Pencocokan, Verifikasi."""


class _Rekam:
    def __init__(self, row):
        self.__dict__.update(dict(row))

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.__dict__}>"


class Kategori(_Rekam):
    def cek_kategori(self) -> bool:
        return bool(getattr(self, "id_kategori", None))


class Lokasi(_Rekam):
    def cek_lokasi(self) -> bool:
        return bool(getattr(self, "id_lokasi", None))


class RiwayatStatus(_Rekam):
    pass


class Pencocokan(_Rekam):
    MENUNGGU = "Menunggu Verifikasi"
    DISETUJUI = "Disetujui"
    DITOLAK = "Ditolak"

    @property
    def menunggu(self) -> bool:
        return self.status_pencocokan == self.MENUNGGU


class Verifikasi(_Rekam):
    pass
