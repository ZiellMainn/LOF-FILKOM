import csv
import io

from .errors import DitolakError


def _aman_csv(nilai):
    """Mencegah CSV/Excel formula injection."""
    teks = "" if nilai is None else str(nilai)
    return "'" + teks if teks[:1] in ("=", "+", "-", "@", "\t", "\r") else teks


class RekapService:
    def __init__(self, repo_rekap, riwayat):
        self.rekap = repo_rekap
        self.riwayat = riwayat

    @staticmethod
    def _cek(pengguna):
        if not pengguna.boleh("rekap"):
            raise DitolakError("Hanya Pimpinan Kemahasiswaan yang dapat melihat rekap.")

    def ringkasan(self, pengguna):
        self._cek(pengguna)
        return self.rekap.ringkasan()

    def riwayat_semua(self, pengguna, **filter):
        self._cek(pengguna)
        return self.riwayat.semua(**filter)

    def ekspor_csv(self, pengguna, **filter) -> str:
        data = self.riwayat_semua(pengguna, batas=5000, **filter)
        out = io.StringIO()
        w = csv.writer(out)
        w.writerow(["Waktu", "ID Laporan", "Barang", "Tipe", "Status", "Diubah oleh"])
        for r in data:
            w.writerow([r.waktu_perubahan, r.id_laporan, _aman_csv(r.nama_barang),
                        r.tipe_laporan, r.status, _aman_csv(r.nama_user)])
        return out.getvalue()
