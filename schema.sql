-- Skema basis data SPBH (LOF-FILKOM). Mengikuti ERD pada BAB 6.
-- Ditulis untuk SQLite; tipe dan constraint dapat dipindah ke MySQL
-- (INTEGER PRIMARY KEY AUTOINCREMENT -> INT AUTO_INCREMENT, TEXT tanggal -> DATETIME).

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS user (
    id_user        INTEGER PRIMARY KEY AUTOINCREMENT,
    nama           TEXT    NOT NULL,
    nim_nip        TEXT    NOT NULL UNIQUE,
    email          TEXT    NOT NULL UNIQUE,
    password_hash  TEXT    NOT NULL,
    no_telp        TEXT,
    role           TEXT    NOT NULL CHECK (role IN
                   ('Civitas Akademika', 'Staf Kemahasiswaan', 'Pimpinan Kemahasiswaan')),
    created_at     TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS kategori (
    id_kategori    INTEGER PRIMARY KEY AUTOINCREMENT,
    nama_kategori  TEXT    NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS lokasi (
    id_lokasi      INTEGER PRIMARY KEY AUTOINCREMENT,
    nama_lokasi    TEXT    NOT NULL,
    jenis_lokasi   TEXT
);

CREATE TABLE IF NOT EXISTS laporan (
    id_laporan     INTEGER PRIMARY KEY AUTOINCREMENT,
    id_user        INTEGER NOT NULL REFERENCES user(id_user),
    id_kategori    INTEGER NOT NULL REFERENCES kategori(id_kategori),
    id_lokasi      INTEGER NOT NULL REFERENCES lokasi(id_lokasi),
    tipe_laporan   TEXT    NOT NULL CHECK (tipe_laporan IN ('Kehilangan', 'Temuan')),
    nama_barang    TEXT    NOT NULL,
    deskripsi      TEXT,
    foto           TEXT,
    waktu_kejadian TEXT    NOT NULL,
    status         TEXT    NOT NULL DEFAULT 'Dilaporkan' CHECK (status IN
                   ('Dilaporkan', 'Dicocokkan', 'Diverifikasi', 'Diambil')),
    created_at     TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);
CREATE INDEX IF NOT EXISTS idx_laporan_tipe_status ON laporan(tipe_laporan, status);
CREATE INDEX IF NOT EXISTS idx_laporan_user ON laporan(id_user);

CREATE TABLE IF NOT EXISTS riwayat_status (
    id_riwayat      INTEGER PRIMARY KEY AUTOINCREMENT,
    id_laporan      INTEGER NOT NULL REFERENCES laporan(id_laporan),
    id_user         INTEGER NOT NULL REFERENCES user(id_user),
    status          TEXT    NOT NULL,
    waktu_perubahan TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);
CREATE INDEX IF NOT EXISTS idx_riwayat_laporan ON riwayat_status(id_laporan);

CREATE TABLE IF NOT EXISTS pencocokan (
    id_pencocokan     INTEGER PRIMARY KEY AUTOINCREMENT,
    id_laporan        INTEGER NOT NULL REFERENCES laporan(id_laporan),
    id_laporan_temuan INTEGER NOT NULL REFERENCES laporan(id_laporan),
    skor_kecocokan    REAL    NOT NULL,
    status_pencocokan TEXT    NOT NULL DEFAULT 'Menunggu Verifikasi' CHECK (status_pencocokan IN
                      ('Menunggu Verifikasi', 'Disetujui', 'Ditolak')),
    waktu_pencocokan  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    UNIQUE (id_laporan, id_laporan_temuan)
);

CREATE TABLE IF NOT EXISTS verifikasi (
    id_verifikasi     INTEGER PRIMARY KEY AUTOINCREMENT,
    id_pencocokan     INTEGER NOT NULL UNIQUE REFERENCES pencocokan(id_pencocokan),
    id_staf           INTEGER NOT NULL REFERENCES user(id_user),
    bukti_kepemilikan TEXT    NOT NULL,
    hasil             TEXT    NOT NULL CHECK (hasil IN ('Disetujui', 'Ditolak')),
    catatan           TEXT,
    waktu_verifikasi  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    waktu_pengambilan TEXT
);
