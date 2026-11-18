# LOF-FILKOM

Sistem Pengelolaan Barang Hilang (SPBH) untuk Fakultas Ilmu Komputer, Universitas Brawijaya.
Mahasiswa dan staf melaporkan barang hilang atau temuan, sistem mencocokkannya secara otomatis,
staf memverifikasi bukti kepemilikan, dan pimpinan memantau rekapnya.

Proyek mata kuliah **Analisis dan Perancangan Sistem**, Teknik Informatika Kelas A, Kelompok 4.
Dosen: Ir. Nurudin Santoso, S.T., M.T.

| Anggota | NIM |
|---|---|
| Ajrina Dinan Apissa | 255150207111014 |
| Nabillah Indah Hikmah Sari | 255150207111011 |
| Intsany Rofilah | 255150207111003 |
| Falisha Quinara Ramadhani | 255150207111005 |

## Fitur

| Kode | Fitur | Halaman |
|---|---|---|
| FR-01 | Login berdasarkan peran (Civitas Akademika, Staf, Pimpinan) | `/login` |
| FR-02 | Buat laporan kehilangan atau temuan, dengan foto | `/laporan/baru` |
| FR-03 | Cari dan saring barang (kata kunci, kategori, lokasi, jenis, status) | `/cari` |
| FR-04 | Pencocokan otomatis berbasis aturan (skor 0-100) | otomatis saat laporan dikirim |
| FR-05 | Verifikasi kepemilikan oleh staf, lalu penyerahan barang | `/verifikasi/` |
| FR-06 | Status laporan dan linimasa, diperbarui otomatis tiap 15 detik | `/status`, `/laporan/<id>` |
| FR-07 | Rekap dan riwayat status, ekspor CSV, untuk pimpinan | `/rekap/`, `/rekap/riwayat` |

Status laporan: **Dilaporkan → Dicocokkan → Diverifikasi → Diambil**.

## Menjalankan

Butuh Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export FLASK_APP=run.py            # Windows PowerShell: $env:FLASK_APP="run.py"
flask seed --reset                 # membuat basis data + data demo
python run.py                      # buka http://127.0.0.1:5000
```

Akun demo (hanya untuk lokal; matikan dengan `TAMPILKAN_AKUN_DEMO=0`):

| Peran | NIM / NIP | Kata sandi |
|---|---|---|
| Civitas Akademika | `255150207111011` | `mahasiswa123` |
| Staf Kemahasiswaan | `198001012005011001` | `staf12345` |
| Pimpinan Kemahasiswaan | `197501012000031001` | `pimpinan123` |

Data demo sudah berisi dua pasangan laporan yang cocok, jadi akun staf langsung punya kandidat untuk diverifikasi.

Tes otomatis:

```bash
pytest
```

## Arsitektur

MVC monolitik. Satu aplikasi web, satu basis data.

```
Browser ── View (templates) ── Controller (blueprints) ── Service ── Repository ── SQLite
                                                              │
                                                       Entity (models)
```

```
app/
  controllers/   Controller: auth, beranda, laporan, pencarian, verifikasi, rekap
  templates/     View: halaman Jinja2 (HalamanLogin, FormLaporan, FormVerifikasi, ...)
  static/        CSS dan JS (tanpa framework, tanpa inline script/style)
  models/        Entity: Pengguna (+3 turunan), Laporan (+2 turunan), Kategori, Lokasi,
                 RiwayatStatus, Pencocokan, Verifikasi
  services/      Control/aturan bisnis: AuthService (ValidasiKredensial), LaporanService
                 (PembuatLaporan), PencocokanService + RuleBasedMatching (PencocokOtomatis),
                 VerifikasiService (PengelolaVerifikasi), RekapService
  repositories/  interfaces.py (abstraksi) + sqlite_repos.py (implementasi)
  container.py   composition root: satu-satunya tempat yang tahu implementasi konkret
schema.sql       skema basis data (sesuai ERD BAB 6)
```

### Penerapan SOLID (BAB 9)

- **SRP**: `LaporanService` mengatur aturan pembuatan laporan, query SQL hanya ada di repository.
- **OCP**: algoritma pencocokan berupa `IMatchingStrategy`. Ganti `RuleBasedMatching` dengan strategi baru tanpa mengubah service.
- **LSP**: `CivitasAkademika`, `StafKemahasiswaan`, `PimpinanKemahasiswaan` dapat dipakai di mana `Pengguna` diharapkan; begitu juga `LaporanKehilangan` dan `LaporanTemuan` terhadap `Laporan`.
- **ISP**: antarmuka kecil dan spesifik (`ILaporanReader`, `ILaporanWriter`, `IMatchingStrategy`, `IVerifikasiRepo`, `IFotoStorage`, ...).
- **DIP**: service hanya bergantung pada `repositories/interfaces.py`, bukan pada SQLite.

### Aturan pencocokan

Skor maksimal 100: kategori sama (40), lokasi sama (25, atau 10 bila satu jenis lokasi), kedekatan waktu
(20, turun bertahap sampai 14 hari), kemiripan kata pada nama dan deskripsi (15). Pasangan dengan skor
di atas `AMBANG_SKOR` (default 50) menjadi kandidat. Laporan milik pengguna yang sama tidak dicocokkan.
Sistem hanya menghasilkan kandidat; keputusan akhir selalu di tangan staf.

## Keamanan

- Kata sandi disimpan sebagai hash (PBKDF2 lewat Werkzeug); login dikunci sementara setelah 5 kali gagal.
- Token CSRF pada semua form POST; sesi di-reset saat login; redirect `next` hanya ke path internal.
- Semua query SQL berparameter; template di-escape otomatis.
- Foto divalidasi ekstensi, ukuran (3 MB), dan isi berkas (magic bytes), disimpan dengan nama acak, dan hanya
  dilayani lewat `/foto/<nama>` setelah login.
- Ciri spesifik, foto, dan lokasi tepat barang **temuan** disembunyikan dari pengguna lain agar klaim palsu tidak
  mudah. Pencarian teks hanya mencari nama barang untuk civitas.
- Header CSP, `X-Frame-Options`, dan `nosniff`; ekspor CSV menetralkan formula injection.
- Izin per peran dicek di controller **dan** di service.

## Produksi

Ganti `SECRET_KEY`, set `SESSION_COOKIE_SECURE=1` (HTTPS), matikan akun demo, dan jangan memakai
`flask seed`. Contoh dengan gunicorn:

```bash
SECRET_KEY=... TAMPILKAN_AKUN_DEMO=0 gunicorn 'run:app'
```

Konfigurasi lain: `DATABASE_PATH`, `UPLOAD_DIR`, `AMBANG_SKOR` (lihat `config.py`). Aplikasi ini butuh server
Python, jadi tidak dapat dihosting statis di Netlify; gunakan Render, Railway, PythonAnywhere, atau sejenisnya.
Untuk pindah ke MySQL, tulis implementasi baru dari `repositories/interfaces.py` dan ubah `container.py`;
`schema.sql` memakai tipe yang mudah dipetakan (lihat komentar di dalamnya).

## Dokumentasi

Diagram rancangan ada di `docs/diagram/`: use case, activity, ERD, arsitektur MVC, robustness, sequence, class,
navigasi, wireframe, dan high-fidelity. Dokumen rancangan lengkap ada pada DPPL kelompok.

## Catatan batasan

- Notifikasi email/WhatsApp belum ada; pengguna memantau lewat halaman status.
- Satu laporan yang sudah `Diverifikasi` tidak dapat dibatalkan dari antarmuka (keputusan staf final).
- Basis data demo memakai SQLite; untuk beban nyata gunakan MySQL/PostgreSQL.
