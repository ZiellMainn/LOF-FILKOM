import os
from datetime import datetime, timedelta

from .errors import ValidasiError, DitolakError

TIPE_VALID = ("Kehilangan", "Temuan")


class LaporanService:
    """PembuatLaporan: validasi, simpan laporan, catat riwayat, lalu memicu pencocokan."""

    def __init__(self, reader, writer, riwayat, master, pencocokan_service, foto_storage, uow):
        self.reader = reader              # ILaporanReader
        self.writer = writer              # ILaporanWriter
        self.riwayat = riwayat
        self.master = master              # IMasterRepo
        self.pencocokan = pencocokan_service
        self.foto = foto_storage          # IFotoStorage
        self.uow = uow

    # --- validasi
    def validasi_data(self, data: dict) -> dict:
        err = {}
        if data.get("tipe_laporan") not in TIPE_VALID:
            err["tipe_laporan"] = "Pilih tipe laporan: Kehilangan atau Temuan."
        nama = (data.get("nama_barang") or "").strip()
        if not 3 <= len(nama) <= 100:
            err["nama_barang"] = "Nama barang wajib diisi (3-100 karakter)."
        desk = (data.get("deskripsi") or "").strip()
        if len(desk) < 10:
            err["deskripsi"] = "Deskripsi minimal 10 karakter agar mudah dicocokkan."
        elif len(desk) > 1000:
            err["deskripsi"] = "Deskripsi maksimal 1000 karakter."
        if not self._angka(data.get("id_kategori")) or not self.master.ambil_kategori(self._angka(data.get("id_kategori"))):
            err["id_kategori"] = "Pilih kategori yang tersedia."
        if not self._angka(data.get("id_lokasi")) or not self.master.ambil_lokasi(self._angka(data.get("id_lokasi"))):
            err["id_lokasi"] = "Pilih lokasi yang tersedia."
        try:
            self._parse_waktu(data.get("waktu_kejadian"))
        except ValueError as e:
            err["waktu_kejadian"] = str(e)
        return err

    @staticmethod
    def _angka(nilai):
        try:
            return int(nilai)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_waktu(teks):
        if not teks:
            raise ValueError("Waktu kejadian wajib diisi.")
        for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                w = datetime.strptime(teks, fmt)
                break
            except ValueError:
                w = None
        if w is None:
            raise ValueError("Format waktu tidak valid.")
        if w > datetime.now() + timedelta(minutes=5):
            raise ValueError("Waktu kejadian tidak boleh di masa depan.")
        if w < datetime.now() - timedelta(days=730):
            raise ValueError("Waktu kejadian terlalu lama (maksimal 2 tahun).")
        return w.strftime("%Y-%m-%d %H:%M:00")

    # --- use case
    def buat_laporan(self, data: dict, pengguna, berkas_foto=None) -> dict:
        if not pengguna.boleh("lapor"):
            raise DitolakError("Peran Anda tidak dapat membuat laporan.")
        err = self.validasi_data(data)
        if err:
            raise ValidasiError(err)
        nama_foto = None
        if berkas_foto is not None and berkas_foto.filename:
            nama_foto = self.foto.simpan(berkas_foto)  # dapat melempar ValidasiError
        try:
            id_laporan = self.writer.simpan({
                "id_user": pengguna.id_user,
                "id_kategori": int(data["id_kategori"]),
                "id_lokasi": int(data["id_lokasi"]),
                "tipe_laporan": data["tipe_laporan"],
                "nama_barang": data["nama_barang"].strip(),
                "deskripsi": data["deskripsi"].strip(),
                "foto": nama_foto,
                "waktu_kejadian": self._parse_waktu(data["waktu_kejadian"]),
            })
            self.riwayat.catat(id_laporan, "Dilaporkan", pengguna.id_user)
            kandidat = self.pencocokan.jalankan_matching(id_laporan, pengguna.id_user)
            self.uow.commit()
        except Exception:
            self.uow.rollback()
            if nama_foto:
                try:
                    os.remove(os.path.join(self.foto.folder, nama_foto))
                except OSError:
                    pass
            raise
        return {"id_laporan": id_laporan, "kandidat": kandidat}

    # --- baca
    def ambil_untuk(self, id_laporan, pengguna):
        """Mengembalikan (laporan, tampil_penuh). Ciri spesifik barang temuan disembunyikan dari
        pengguna lain agar klaim palsu tidak mudah."""
        laporan = self.reader.ambil(id_laporan)
        if laporan is None:
            return None, False
        penuh = (laporan.get_tipe() == "Kehilangan" or laporan.milik(pengguna.id_user)
                 or pengguna.boleh("lihat_detail"))
        return laporan, penuh

    def ambil_foto_untuk(self, nama_foto, pengguna):
        """Nama berkas foto bila pengguna boleh melihatnya, selain itu None."""
        laporan = self.reader.ambil_by_foto(nama_foto)
        if laporan is None:
            return None
        penuh = (laporan.get_tipe() == "Kehilangan" or laporan.milik(pengguna.id_user)
                 or pengguna.boleh("lihat_detail"))
        return nama_foto if penuh else None

    def cari(self, pengguna, **filter):
        return self.reader.cari(cari_deskripsi=pengguna.boleh("lihat_detail"), **filter)
