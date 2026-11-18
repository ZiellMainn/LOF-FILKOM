"""Composition root: satu-satunya tempat yang mengetahui implementasi konkret."""
from flask import current_app, g

from .db import get_db
from .repositories.sqlite_repos import (
    SqliteUnitOfWork, PenggunaRepoSqlite, MasterRepoSqlite, LaporanRepoSqlite, RiwayatRepoSqlite,
    PencocokanRepoSqlite, VerifikasiRepoSqlite, RekapRepoSqlite,
)
from .services.auth_service import AuthService
from .services.foto_storage import FotoStorageLokal
from .services.laporan_service import LaporanService
from .services.matching import RuleBasedMatching
from .services.pencocokan_service import PencocokanService
from .services.rekap_service import RekapService
from .services.verifikasi_service import VerifikasiService


class Layanan:
    def __init__(self, db, cfg):
        uow = SqliteUnitOfWork(db)
        self.pengguna = PenggunaRepoSqlite(db)
        self.master = MasterRepoSqlite(db)
        laporan_repo = LaporanRepoSqlite(db)
        self.laporan_repo = laporan_repo
        self.riwayat = RiwayatRepoSqlite(db)
        self.pencocokan_repo = PencocokanRepoSqlite(db)
        verifikasi_repo = VerifikasiRepoSqlite(db)

        self.auth = AuthService(self.pengguna, cfg["LOGIN_MAKS_GAGAL"], cfg["LOGIN_KUNCI_DETIK"])
        pencocokan = PencocokanService(laporan_repo, laporan_repo, self.riwayat, self.pencocokan_repo,
                                       RuleBasedMatching(), cfg["AMBANG_SKOR"])
        self.laporan = LaporanService(laporan_repo, laporan_repo, self.riwayat, self.master, pencocokan,
                                      FotoStorageLokal(cfg["UPLOAD_DIR"]), uow)
        self.verifikasi = VerifikasiService(self.pencocokan_repo, verifikasi_repo, laporan_repo,
                                            self.riwayat, uow)
        self.rekap = RekapService(RekapRepoSqlite(db), self.riwayat)


def layanan() -> Layanan:
    if "layanan" not in g:
        g.layanan = Layanan(get_db(), current_app.config)
    return g.layanan
