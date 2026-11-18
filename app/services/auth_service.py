import time

from werkzeug.security import check_password_hash

from ..models import Pengguna
from .errors import KredensialError


class AuthService:
    """ValidasiKredensial: mencocokkan NIM/NIP dan kata sandi. Gagal berulang mengunci sementara."""

    _gagal = {}  # nim_nip -> (jumlah, waktu_terakhir); sederhana, per proses

    def __init__(self, repo_pengguna, maks_gagal=5, kunci_detik=300):
        self.repo = repo_pengguna
        self.maks_gagal = maks_gagal
        self.kunci_detik = kunci_detik

    def login(self, nim_nip: str, kata_sandi: str) -> Pengguna:
        nim_nip = (nim_nip or "").strip()
        if not nim_nip or not kata_sandi:
            raise KredensialError("NIM/NIP dan kata sandi wajib diisi.")
        self._cek_kunci(nim_nip)
        row = self.repo.cari_by_nim_nip(nim_nip)
        # check_password_hash dijalankan walau akun tidak ada agar waktu respons relatif sama
        hash_pakai = row["password_hash"] if row else "pbkdf2:sha256:600000$x$0"
        cocok = check_password_hash(hash_pakai, kata_sandi) and row is not None
        if not cocok:
            self._catat_gagal(nim_nip)
            raise KredensialError("NIM/NIP atau kata sandi salah.")
        self._gagal.pop(nim_nip, None)
        return Pengguna.dari_row(row)

    def _cek_kunci(self, nim_nip):
        jumlah, terakhir = self._gagal.get(nim_nip, (0, 0))
        if jumlah >= self.maks_gagal:
            if time.time() - terakhir < self.kunci_detik:
                raise KredensialError("Terlalu banyak percobaan gagal. Coba lagi beberapa menit lagi.")
            self._gagal.pop(nim_nip, None)

    def _catat_gagal(self, nim_nip):
        jumlah, _ = self._gagal.get(nim_nip, (0, 0))
        self._gagal[nim_nip] = (jumlah + 1, time.time())

    @classmethod
    def reset(cls):
        cls._gagal.clear()
