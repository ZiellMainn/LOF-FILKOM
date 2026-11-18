"""Abstraksi (interface) yang dipakai Service. Service hanya bergantung pada modul ini,
bukan pada implementasi database (Dependency Inversion Principle)."""
from abc import ABC, abstractmethod


class IUnitOfWork(ABC):
    @abstractmethod
    def commit(self): ...

    @abstractmethod
    def rollback(self): ...


class IPenggunaRepo(ABC):
    @abstractmethod
    def cari_by_nim_nip(self, nim_nip): ...

    @abstractmethod
    def ambil(self, id_user): ...


class IMasterRepo(ABC):
    @abstractmethod
    def daftar_kategori(self): ...

    @abstractmethod
    def daftar_lokasi(self): ...

    @abstractmethod
    def ambil_kategori(self, id_kategori): ...

    @abstractmethod
    def ambil_lokasi(self, id_lokasi): ...


class ILaporanReader(ABC):
    @abstractmethod
    def ambil(self, id_laporan): ...

    @abstractmethod
    def cari(self, **filter): ...

    @abstractmethod
    def milik_user(self, id_user): ...

    @abstractmethod
    def terbaru(self, batas): ...

    @abstractmethod
    def ambil_laporan_lawan(self, laporan): ...

    @abstractmethod
    def ambil_by_foto(self, nama_foto): ...


class ILaporanWriter(ABC):
    @abstractmethod
    def simpan(self, data) -> int: ...

    @abstractmethod
    def ubah_status(self, id_laporan, status): ...


class IRiwayatRepo(ABC):
    @abstractmethod
    def catat(self, id_laporan, status, id_user): ...

    @abstractmethod
    def daftar(self, id_laporan): ...

    @abstractmethod
    def semua(self, **filter): ...


class IPencocokanRepo(ABC):
    @abstractmethod
    def simpan_kandidat(self, id_kehilangan, id_temuan, skor): ...

    @abstractmethod
    def ambil(self, id_pencocokan): ...

    @abstractmethod
    def daftar(self, status): ...

    @abstractmethod
    def by_laporan(self, id_laporan): ...

    @abstractmethod
    def ubah_status(self, id_pencocokan, status): ...


class IVerifikasiRepo(ABC):
    @abstractmethod
    def simpan(self, id_pencocokan, id_staf, bukti, hasil, catatan): ...

    @abstractmethod
    def ambil_by_pencocokan(self, id_pencocokan): ...

    @abstractmethod
    def set_pengambilan(self, id_pencocokan): ...


class IRekapRepo(ABC):
    @abstractmethod
    def ringkasan(self): ...


class IMatchingStrategy(ABC):
    """Strategi penghitung skor kecocokan dua laporan (OCP: tambah class baru, jangan ubah service)."""

    @abstractmethod
    def hitung_skor(self, laporan_a, laporan_b) -> float: ...


class IFotoStorage(ABC):
    @abstractmethod
    def simpan(self, berkas) -> str: ...
