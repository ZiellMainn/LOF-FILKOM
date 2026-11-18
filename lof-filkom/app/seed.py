"""Data demo. Kata sandi di sini HANYA untuk pengembangan lokal; jangan dipakai di produksi."""
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash

KATEGORI = ["Elektronik", "Dokumen & Kartu", "Dompet & Tas", "Kunci", "Pakaian & Aksesori",
            "Alat Tulis & Buku", "Lainnya"]

LOKASI = [
    ("Gedung A", "Gedung"), ("Gedung B", "Gedung"), ("Gedung F", "Gedung"),
    ("Perpustakaan FILKOM", "Gedung"), ("Kantin FILKOM", "Kantin"), ("Parkiran Motor", "Parkiran"),
    ("Masjid Kampus", "Ibadah"), ("Laboratorium Komputer", "Gedung"), ("Taman FILKOM", "Taman"),
]

AKUN = [
    ("Nabillah Indah Hikmah Sari", "255150207111011", "nabillah@student.ub.ac.id", "mahasiswa123", "Civitas Akademika"),
    ("Falisha Quinara Ramadhani", "255150207111005", "falisha@student.ub.ac.id", "mahasiswa123", "Civitas Akademika"),
    ("Intsany Rofilah", "255150207111003", "intsany@student.ub.ac.id", "mahasiswa123", "Civitas Akademika"),
    ("Ajrina Dinan Apissa", "255150207111014", "ajrina@student.ub.ac.id", "mahasiswa123", "Civitas Akademika"),
    ("Staf Kemahasiswaan FILKOM", "198001012005011001", "staf@filkom.ub.ac.id", "staf12345", "Staf Kemahasiswaan"),
    ("Pimpinan Kemahasiswaan FILKOM", "197501012000031001", "pimpinan@filkom.ub.ac.id", "pimpinan123", "Pimpinan Kemahasiswaan"),
]

# (pelapor_index, tipe, nama, kategori, lokasi, deskripsi, hari_lalu)
LAPORAN = [
    (0, "Kehilangan", "Dompet kulit cokelat", "Dompet & Tas", "Kantin FILKOM",
     "Dompet kulit cokelat berisi KTM dan beberapa kartu, hilang saat makan siang.", 2),
    (1, "Temuan", "Dompet cokelat", "Dompet & Tas", "Kantin FILKOM",
     "Dompet kulit cokelat ditemukan di bawah meja kantin, ada kartu di dalamnya.", 1),
    (2, "Kehilangan", "Earphone nirkabel putih", "Elektronik", "Perpustakaan FILKOM",
     "Earphone nirkabel putih dengan casing kecil, tertinggal di meja lantai dua.", 4),
    (3, "Kehilangan", "Kunci motor Honda", "Kunci", "Parkiran Motor",
     "Kunci motor Honda dengan gantungan kunci beruang, hilang di area parkir.", 3),
    (1, "Temuan", "Kunci motor gantungan beruang", "Kunci", "Parkiran Motor",
     "Kunci motor dengan gantungan boneka beruang ditemukan di dekat pos satpam parkiran.", 2),
    (3, "Temuan", "Jaket hitam", "Pakaian & Aksesori", "Gedung F",
     "Jaket hitam ukuran L tertinggal di ruang kelas lantai tiga.", 5),
    (0, "Kehilangan", "Charger laptop 65W", "Elektronik", "Laboratorium Komputer",
     "Charger laptop 65W kabel hitam, tertinggal di laboratorium setelah praktikum.", 1),
    (2, "Temuan", "Botol minum biru", "Lainnya", "Taman FILKOM",
     "Botol minum warna biru tua ditemukan di bangku taman.", 6),
]


def isi_data_demo(db):
    for nama in KATEGORI:
        db.execute("INSERT OR IGNORE INTO kategori (nama_kategori) VALUES (?)", (nama,))
    if db.execute("SELECT COUNT(*) FROM lokasi").fetchone()[0] == 0:
        db.executemany("INSERT INTO lokasi (nama_lokasi, jenis_lokasi) VALUES (?,?)", LOKASI)
    ids = []
    for nama, nim, email, sandi, role in AKUN:
        db.execute(
            "INSERT OR IGNORE INTO user (nama, nim_nip, email, password_hash, role) VALUES (?,?,?,?,?)",
            (nama, nim, email, generate_password_hash(sandi), role))
        ids.append(db.execute("SELECT id_user FROM user WHERE nim_nip = ?", (nim,)).fetchone()[0])
    if db.execute("SELECT COUNT(*) FROM laporan").fetchone()[0] == 0:
        # Pakai layanan sungguhan agar data demo ikut melewati validasi dan pencocokan.
        from .services.laporan_service import LaporanService
        from .services.matching import RuleBasedMatching
        from .services.pencocokan_service import PencocokanService
        from .repositories.sqlite_repos import (LaporanRepoSqlite, RiwayatRepoSqlite, PencocokanRepoSqlite,
                                                MasterRepoSqlite, SqliteUnitOfWork, PenggunaRepoSqlite)
        lap, riw = LaporanRepoSqlite(db), RiwayatRepoSqlite(db)
        pen = PencocokanService(lap, lap, riw, PencocokanRepoSqlite(db), RuleBasedMatching(), 50)
        master = MasterRepoSqlite(db)
        svc = LaporanService(lap, lap, riw, master, pen, None, SqliteUnitOfWork(db))
        kat = {k.nama_kategori: k.id_kategori for k in master.daftar_kategori()}
        lok = {x.nama_lokasi: x.id_lokasi for x in master.daftar_lokasi()}
        pengguna = PenggunaRepoSqlite(db)
        for idx, tipe, nama, kategori, lokasi, desk, hari in LAPORAN:
            waktu = (datetime.now() - timedelta(days=hari, hours=1)).strftime("%Y-%m-%dT%H:%M")
            svc.buat_laporan({"tipe_laporan": tipe, "nama_barang": nama, "id_kategori": kat[kategori],
                              "id_lokasi": lok[lokasi], "waktu_kejadian": waktu, "deskripsi": desk},
                             pengguna.ambil(ids[idx]))
    db.commit()
