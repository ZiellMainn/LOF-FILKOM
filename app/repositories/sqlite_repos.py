"""Implementasi repository untuk SQLite. Semua query memakai parameter (tanpa string concat)."""
from ..models import (
    Pengguna, Laporan, Kategori, Lokasi, RiwayatStatus, Pencocokan, Verifikasi,
)
from .interfaces import (
    IUnitOfWork, IPenggunaRepo, IMasterRepo, ILaporanReader, ILaporanWriter,
    IRiwayatRepo, IPencocokanRepo, IVerifikasiRepo, IRekapRepo,
)

_LAPORAN_SELECT = """
    SELECT l.*, k.nama_kategori, lo.nama_lokasi, lo.jenis_lokasi, u.nama AS nama_pelapor
    FROM laporan l
    JOIN kategori k  ON k.id_kategori = l.id_kategori
    JOIN lokasi   lo ON lo.id_lokasi  = l.id_lokasi
    JOIN user     u  ON u.id_user     = l.id_user
"""


class SqliteUnitOfWork(IUnitOfWork):
    def __init__(self, db):
        self.db = db

    def commit(self):
        self.db.commit()

    def rollback(self):
        self.db.rollback()


class PenggunaRepoSqlite(IPenggunaRepo):
    def __init__(self, db):
        self.db = db

    def cari_by_nim_nip(self, nim_nip):
        return self.db.execute("SELECT * FROM user WHERE nim_nip = ?", (nim_nip,)).fetchone()

    def ambil(self, id_user):
        row = self.db.execute("SELECT * FROM user WHERE id_user = ?", (id_user,)).fetchone()
        return Pengguna.dari_row(row) if row else None


class MasterRepoSqlite(IMasterRepo):
    def __init__(self, db):
        self.db = db

    def daftar_kategori(self):
        rows = self.db.execute("SELECT * FROM kategori ORDER BY nama_kategori").fetchall()
        return [Kategori(r) for r in rows]

    def daftar_lokasi(self):
        rows = self.db.execute("SELECT * FROM lokasi ORDER BY jenis_lokasi, nama_lokasi").fetchall()
        return [Lokasi(r) for r in rows]

    def ambil_kategori(self, id_kategori):
        r = self.db.execute("SELECT * FROM kategori WHERE id_kategori = ?", (id_kategori,)).fetchone()
        return Kategori(r) if r else None

    def ambil_lokasi(self, id_lokasi):
        r = self.db.execute("SELECT * FROM lokasi WHERE id_lokasi = ?", (id_lokasi,)).fetchone()
        return Lokasi(r) if r else None


class LaporanRepoSqlite(ILaporanReader, ILaporanWriter):
    """Satu implementasi untuk dua interface kecil (ISP): reader dan writer."""

    def __init__(self, db):
        self.db = db

    # --- ILaporanReader
    def ambil(self, id_laporan):
        r = self.db.execute(_LAPORAN_SELECT + " WHERE l.id_laporan = ?", (id_laporan,)).fetchone()
        return Laporan.dari_row(r) if r else None

    def cari(self, q=None, id_kategori=None, id_lokasi=None, tipe=None, status=None,
             cari_deskripsi=False, sembunyikan_selesai=True, batas=60):
        sql, args = _LAPORAN_SELECT + " WHERE 1=1", []
        if q:
            pola = f"%{q}%"
            if cari_deskripsi:
                sql += " AND (l.nama_barang LIKE ? OR l.deskripsi LIKE ?)"
                args += [pola, pola]
            else:
                sql += " AND l.nama_barang LIKE ?"
                args.append(pola)
        if id_kategori:
            sql += " AND l.id_kategori = ?"
            args.append(id_kategori)
        if id_lokasi:
            sql += " AND l.id_lokasi = ?"
            args.append(id_lokasi)
        if tipe:
            sql += " AND l.tipe_laporan = ?"
            args.append(tipe)
        if status:
            sql += " AND l.status = ?"
            args.append(status)
        elif sembunyikan_selesai:
            sql += " AND l.status <> 'Diambil'"
        sql += " ORDER BY l.waktu_kejadian DESC, l.id_laporan DESC LIMIT ?"
        args.append(batas)
        return [Laporan.dari_row(r) for r in self.db.execute(sql, args).fetchall()]

    def milik_user(self, id_user):
        rows = self.db.execute(
            _LAPORAN_SELECT + " WHERE l.id_user = ? ORDER BY l.created_at DESC, l.id_laporan DESC",
            (id_user,)).fetchall()
        return [Laporan.dari_row(r) for r in rows]

    def terbaru(self, batas=6):
        rows = self.db.execute(
            _LAPORAN_SELECT + " WHERE l.status <> 'Diambil' ORDER BY l.created_at DESC, l.id_laporan DESC LIMIT ?",
            (batas,)).fetchall()
        return [Laporan.dari_row(r) for r in rows]

    def ambil_laporan_lawan(self, laporan):
        lawan = "Temuan" if laporan.get_tipe() == "Kehilangan" else "Kehilangan"
        rows = self.db.execute(
            _LAPORAN_SELECT + " WHERE l.tipe_laporan = ? AND l.status IN ('Dilaporkan','Dicocokkan')",
            (lawan,)).fetchall()
        return [Laporan.dari_row(r) for r in rows]

    def ambil_by_foto(self, nama_foto):
        r = self.db.execute(_LAPORAN_SELECT + " WHERE l.foto = ?", (nama_foto,)).fetchone()
        return Laporan.dari_row(r) if r else None

    # --- ILaporanWriter
    def simpan(self, d):
        cur = self.db.execute(
            """INSERT INTO laporan (id_user, id_kategori, id_lokasi, tipe_laporan, nama_barang,
                                    deskripsi, foto, waktu_kejadian, status)
               VALUES (?,?,?,?,?,?,?,?, 'Dilaporkan')""",
            (d["id_user"], d["id_kategori"], d["id_lokasi"], d["tipe_laporan"], d["nama_barang"],
             d["deskripsi"], d.get("foto"), d["waktu_kejadian"]))
        return cur.lastrowid

    def ubah_status(self, id_laporan, status):
        self.db.execute("UPDATE laporan SET status = ? WHERE id_laporan = ?", (status, id_laporan))


class RiwayatRepoSqlite(IRiwayatRepo):
    def __init__(self, db):
        self.db = db

    def catat(self, id_laporan, status, id_user):
        self.db.execute("INSERT INTO riwayat_status (id_laporan, id_user, status) VALUES (?,?,?)",
                        (id_laporan, id_user, status))

    def daftar(self, id_laporan):
        rows = self.db.execute(
            """SELECT r.*, u.nama AS nama_user, u.role FROM riwayat_status r
               JOIN user u ON u.id_user = r.id_user
               WHERE r.id_laporan = ? ORDER BY r.waktu_perubahan, r.id_riwayat""",
            (id_laporan,)).fetchall()
        return [RiwayatStatus(r) for r in rows]

    def semua(self, status=None, tipe=None, dari=None, sampai=None, batas=300):
        sql = """SELECT r.*, u.nama AS nama_user, l.nama_barang, l.tipe_laporan
                 FROM riwayat_status r
                 JOIN user u ON u.id_user = r.id_user
                 JOIN laporan l ON l.id_laporan = r.id_laporan WHERE 1=1"""
        args = []
        if status:
            sql += " AND r.status = ?"
            args.append(status)
        if tipe:
            sql += " AND l.tipe_laporan = ?"
            args.append(tipe)
        if dari:
            sql += " AND date(r.waktu_perubahan) >= date(?)"
            args.append(dari)
        if sampai:
            sql += " AND date(r.waktu_perubahan) <= date(?)"
            args.append(sampai)
        sql += " ORDER BY r.waktu_perubahan DESC, r.id_riwayat DESC LIMIT ?"
        args.append(batas)
        return [RiwayatStatus(r) for r in self.db.execute(sql, args).fetchall()]


_PENCOCOKAN_SELECT = """
    SELECT p.*,
           lk.nama_barang AS nama_kehilangan, lk.deskripsi AS deskripsi_kehilangan,
           lk.foto AS foto_kehilangan, lk.waktu_kejadian AS waktu_kehilangan, lk.status AS status_kehilangan,
           uk.nama AS nama_pemilik, uk.nim_nip AS nim_pemilik, uk.no_telp AS telp_pemilik,
           kk.nama_kategori, lok.nama_lokasi AS lokasi_kehilangan,
           lt.nama_barang AS nama_temuan, lt.deskripsi AS deskripsi_temuan,
           lt.foto AS foto_temuan, lt.waktu_kejadian AS waktu_temuan, lt.status AS status_temuan,
           ut.nama AS nama_penemu, lot.nama_lokasi AS lokasi_temuan
    FROM pencocokan p
    JOIN laporan lk ON lk.id_laporan = p.id_laporan
    JOIN user uk ON uk.id_user = lk.id_user
    JOIN kategori kk ON kk.id_kategori = lk.id_kategori
    JOIN lokasi lok ON lok.id_lokasi = lk.id_lokasi
    JOIN laporan lt ON lt.id_laporan = p.id_laporan_temuan
    JOIN user ut ON ut.id_user = lt.id_user
    JOIN lokasi lot ON lot.id_lokasi = lt.id_lokasi
"""


class PencocokanRepoSqlite(IPencocokanRepo):
    def __init__(self, db):
        self.db = db

    def simpan_kandidat(self, id_kehilangan, id_temuan, skor):
        """Mengembalikan True bila ini kandidat baru."""
        ada = self.db.execute(
            "SELECT 1 FROM pencocokan WHERE id_laporan = ? AND id_laporan_temuan = ?",
            (id_kehilangan, id_temuan)).fetchone()
        if ada:
            return False
        self.db.execute(
            "INSERT INTO pencocokan (id_laporan, id_laporan_temuan, skor_kecocokan) VALUES (?,?,?)",
            (id_kehilangan, id_temuan, round(skor, 2)))
        return True

    def ambil(self, id_pencocokan):
        r = self.db.execute(_PENCOCOKAN_SELECT + " WHERE p.id_pencocokan = ?", (id_pencocokan,)).fetchone()
        return Pencocokan(r) if r else None

    def daftar(self, status=None):
        sql, args = _PENCOCOKAN_SELECT, []
        if status:
            sql += " WHERE p.status_pencocokan = ?"
            args.append(status)
        sql += " ORDER BY p.skor_kecocokan DESC, p.id_pencocokan"
        return [Pencocokan(r) for r in self.db.execute(sql, args).fetchall()]

    def by_laporan(self, id_laporan):
        rows = self.db.execute(
            _PENCOCOKAN_SELECT + " WHERE p.id_laporan = ? OR p.id_laporan_temuan = ? ORDER BY p.skor_kecocokan DESC",
            (id_laporan, id_laporan)).fetchall()
        return [Pencocokan(r) for r in rows]

    def ubah_status(self, id_pencocokan, status):
        self.db.execute("UPDATE pencocokan SET status_pencocokan = ? WHERE id_pencocokan = ?",
                        (status, id_pencocokan))


class VerifikasiRepoSqlite(IVerifikasiRepo):
    def __init__(self, db):
        self.db = db

    def simpan(self, id_pencocokan, id_staf, bukti, hasil, catatan):
        self.db.execute(
            """INSERT INTO verifikasi (id_pencocokan, id_staf, bukti_kepemilikan, hasil, catatan)
               VALUES (?,?,?,?,?)""", (id_pencocokan, id_staf, bukti, hasil, catatan))

    def ambil_by_pencocokan(self, id_pencocokan):
        r = self.db.execute(
            """SELECT v.*, u.nama AS nama_staf FROM verifikasi v JOIN user u ON u.id_user = v.id_staf
               WHERE v.id_pencocokan = ?""", (id_pencocokan,)).fetchone()
        return Verifikasi(r) if r else None

    def set_pengambilan(self, id_pencocokan):
        self.db.execute(
            "UPDATE verifikasi SET waktu_pengambilan = datetime('now','localtime') WHERE id_pencocokan = ?",
            (id_pencocokan,))


class RekapRepoSqlite(IRekapRepo):
    def __init__(self, db):
        self.db = db

    def _hitung(self, sql, args=()):
        return [dict(r) for r in self.db.execute(sql, args).fetchall()]

    def ringkasan(self):
        total = self.db.execute("SELECT COUNT(*) FROM laporan").fetchone()[0]
        per_tipe = self._hitung("SELECT tipe_laporan AS label, COUNT(*) AS jumlah FROM laporan GROUP BY tipe_laporan")
        per_status = self._hitung("SELECT status AS label, COUNT(*) AS jumlah FROM laporan GROUP BY status")
        per_kategori = self._hitung(
            """SELECT k.nama_kategori AS label, COUNT(*) AS jumlah FROM laporan l
               JOIN kategori k ON k.id_kategori = l.id_kategori GROUP BY k.id_kategori ORDER BY jumlah DESC""")
        per_lokasi = self._hitung(
            """SELECT lo.nama_lokasi AS label, COUNT(*) AS jumlah FROM laporan l
               JOIN lokasi lo ON lo.id_lokasi = l.id_lokasi GROUP BY lo.id_lokasi
               ORDER BY jumlah DESC LIMIT 5""")
        per_bulan = self._hitung(
            """SELECT strftime('%Y-%m', created_at) AS label, COUNT(*) AS jumlah FROM laporan
               GROUP BY label ORDER BY label DESC LIMIT 6""")[::-1]
        kehilangan = self.db.execute("SELECT COUNT(*) FROM laporan WHERE tipe_laporan='Kehilangan'").fetchone()[0]
        kembali = self.db.execute(
            "SELECT COUNT(*) FROM laporan WHERE tipe_laporan='Kehilangan' AND status='Diambil'").fetchone()[0]
        menunggu = self.db.execute(
            "SELECT COUNT(*) FROM pencocokan WHERE status_pencocokan='Menunggu Verifikasi'").fetchone()[0]
        return {
            "total": total, "per_tipe": per_tipe, "per_status": per_status, "per_kategori": per_kategori,
            "per_lokasi": per_lokasi, "per_bulan": per_bulan, "menunggu_verifikasi": menunggu,
            "tingkat_pengembalian": round(100 * kembali / kehilangan, 1) if kehilangan else 0.0,
            "kehilangan": kehilangan, "kembali": kembali,
        }
