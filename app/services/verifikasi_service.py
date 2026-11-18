from ..models import Pencocokan
from .errors import ValidasiError, AturanError, DitolakError


class VerifikasiService:
    """PengelolaVerifikasi: staf memutuskan kandidat cocok, lalu menandai barang diambil."""

    def __init__(self, repo_pencocokan, repo_verifikasi, writer, riwayat, uow):
        self.pencocokan = repo_pencocokan
        self.verifikasi = repo_verifikasi   # IVerifikasiRepo
        self.writer = writer
        self.riwayat = riwayat
        self.uow = uow

    @staticmethod
    def _cek_izin(staf):
        if not staf.boleh("verifikasi"):
            raise DitolakError("Hanya Staf Kemahasiswaan yang dapat memverifikasi.")

    def ambil_kandidat(self, staf, status=Pencocokan.MENUNGGU):
        self._cek_izin(staf)
        return self.pencocokan.daftar(status)

    def ambil_detail(self, staf, id_pencocokan):
        self._cek_izin(staf)
        p = self.pencocokan.ambil(id_pencocokan)
        if p is None:
            return None, None
        return p, self.verifikasi.ambil_by_pencocokan(id_pencocokan)

    def verifikasi_klaim(self, id_pencocokan, hasil, bukti, catatan, staf):
        self._cek_izin(staf)
        err = {}
        bukti = (bukti or "").strip()
        catatan = (catatan or "").strip()
        if hasil not in (Pencocokan.DISETUJUI, Pencocokan.DITOLAK):
            err["hasil"] = "Pilih Setujui atau Tolak."
        if len(bukti) < 10:
            err["bukti_kepemilikan"] = "Tuliskan bukti kepemilikan yang diperiksa (minimal 10 karakter)."
        if hasil == Pencocokan.DITOLAK and not catatan:
            err["catatan"] = "Catatan wajib diisi saat menolak agar pengguna tahu alasannya."
        if err:
            raise ValidasiError(err)
        p = self.pencocokan.ambil(id_pencocokan)
        if p is None:
            raise AturanError("Kandidat tidak ditemukan.")
        if not p.menunggu:
            raise AturanError("Kandidat ini sudah diputuskan.")
        try:
            self.verifikasi.simpan(id_pencocokan, staf.id_user, bukti, hasil, catatan or None)
            self.pencocokan.ubah_status(id_pencocokan, hasil)
            ids = (p.id_laporan, p.id_laporan_temuan)
            if hasil == Pencocokan.DISETUJUI:
                for lap in ids:
                    self.writer.ubah_status(lap, "Diverifikasi")
                    self.riwayat.catat(lap, "Diverifikasi", staf.id_user)
                    for lain in self.pencocokan.by_laporan(lap):
                        if lain.id_pencocokan != id_pencocokan and lain.menunggu:
                            self.pencocokan.ubah_status(lain.id_pencocokan, Pencocokan.DITOLAK)
            else:
                for lap in ids:
                    masih = [x for x in self.pencocokan.by_laporan(lap) if x.menunggu]
                    if not masih:
                        self.writer.ubah_status(lap, "Dilaporkan")
                        self.riwayat.catat(lap, "Dilaporkan", staf.id_user)
            self.uow.commit()
        except Exception:
            self.uow.rollback()
            raise

    def tandai_diambil(self, id_pencocokan, staf):
        self._cek_izin(staf)
        p = self.pencocokan.ambil(id_pencocokan)
        v = self.verifikasi.ambil_by_pencocokan(id_pencocokan)
        if p is None or v is None or v.hasil != Pencocokan.DISETUJUI:
            raise AturanError("Barang hanya dapat diserahkan setelah verifikasi disetujui.")
        if v.waktu_pengambilan:
            raise AturanError("Barang ini sudah ditandai diambil.")
        try:
            self.verifikasi.set_pengambilan(id_pencocokan)
            for lap in (p.id_laporan, p.id_laporan_temuan):
                self.writer.ubah_status(lap, "Diambil")
                self.riwayat.catat(lap, "Diambil", staf.id_user)
            self.uow.commit()
        except Exception:
            self.uow.rollback()
            raise
