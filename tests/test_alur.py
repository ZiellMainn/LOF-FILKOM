"""Uji alur utama: login, buat laporan, pencocokan, verifikasi, rekap, serta aturan keamanan."""
import io
from datetime import datetime, timedelta

from app.db import get_db
from conftest import MHS, MHS2, STAF, PIMPINAN


def waktu(jam_lalu=2):
    return (datetime.now() - timedelta(hours=jam_lalu)).strftime("%Y-%m-%dT%H:%M")


def kirim_laporan(k, tipe, nama="Dompet cokelat", kat=3, lok=5, desk="Dompet kulit cokelat berisi kartu", foto=None):
    data = {"tipe_laporan": tipe, "nama_barang": nama, "id_kategori": kat, "id_lokasi": lok,
            "waktu_kejadian": waktu(), "deskripsi": desk}
    if foto is not None:
        data["foto"] = foto
    return k.post("/laporan/baru", data, content_type="multipart/form-data")


def id_kategori(app, nama):
    with app.app_context():
        return get_db().execute("SELECT id_kategori FROM kategori WHERE nama_kategori=?", (nama,)).fetchone()[0]


def id_lokasi(app, nama):
    with app.app_context():
        return get_db().execute("SELECT id_lokasi FROM lokasi WHERE nama_lokasi=?", (nama,)).fetchone()[0]


def test_halaman_butuh_login(baru):
    k = baru()
    for url in ("/", "/cari", "/status", "/laporan/baru", "/verifikasi/", "/rekap/"):
        r = k.c.get(url)
        assert r.status_code == 302 and "/login" in r.headers["Location"]


def test_login_salah_dan_benar(baru):
    k = baru()
    r = k.login(MHS[0], "salah")
    assert r.status_code == 200 and "salah" in r.get_data(as_text=True)
    assert k.login(*MHS).status_code == 302
    assert "Halo" in k.c.get("/").get_data(as_text=True)


def test_login_terkunci_setelah_gagal_berulang(baru):
    k = baru()
    for _ in range(5):
        k.login(MHS[0], "salah")
    assert "Terlalu banyak" in k.login(*MHS).get_data(as_text=True)


def test_csrf_wajib_pada_post(baru):
    k = baru()
    assert k.c.post("/login", data={"nim_nip": MHS[0], "kata_sandi": MHS[1]}).status_code == 400


def test_open_redirect_diblokir(baru):
    k = baru()
    k.login(*MHS)
    k2 = baru()
    r = k2.c.post("/login?next=//jahat.example", data={"nim_nip": MHS[0], "kata_sandi": MHS[1], "_csrf": k2.token()})
    assert r.headers["Location"] == "/"


def test_validasi_form_laporan(baru):
    k = baru()
    k.login(*MHS)
    r = k.post("/laporan/baru", {"tipe_laporan": "Kehilangan", "nama_barang": "a", "deskripsi": "pendek",
                                 "id_kategori": "", "id_lokasi": "999", "waktu_kejadian": ""})
    html = r.get_data(as_text=True)
    assert r.status_code == 200
    for pesan in ("Nama barang wajib", "Deskripsi minimal", "Pilih kategori", "Pilih lokasi", "Waktu kejadian wajib"):
        assert pesan in html


def test_waktu_masa_depan_ditolak(baru):
    k = baru()
    k.login(*MHS)
    masa_depan = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
    r = k.post("/laporan/baru", {"tipe_laporan": "Kehilangan", "nama_barang": "Payung", "id_kategori": 1,
                                 "id_lokasi": 1, "waktu_kejadian": masa_depan, "deskripsi": "Payung lipat hitam"})
    assert "masa depan" in r.get_data(as_text=True)


def test_alur_lengkap_pencocokan_sampai_diambil(app, baru):
    kat, lok = id_kategori(app, "Dompet & Tas"), id_lokasi(app, "Kantin FILKOM")
    pemilik, penemu, staf, pimpinan = baru(), baru(), baru(), baru()
    pemilik.login(*MHS)
    penemu.login(*MHS2)
    staf.login(*STAF)
    pimpinan.login(*PIMPINAN)

    r = kirim_laporan(pemilik, "Kehilangan", kat=kat, lok=lok)
    assert r.status_code == 302 and "konfirmasi" in r.headers["Location"]
    with app.app_context():
        assert get_db().execute("SELECT status FROM laporan WHERE id_laporan=1").fetchone()[0] == "Dilaporkan"

    # laporan lawan dari pengguna lain memicu pencocokan
    r = kirim_laporan(penemu, "Temuan", nama="Dompet kulit", kat=kat, lok=lok,
                      desk="Dompet kulit cokelat ditemukan di kantin berisi kartu")
    assert "kandidat=1" in r.headers["Location"]
    with app.app_context():
        db = get_db()
        assert db.execute("SELECT COUNT(*) FROM pencocokan").fetchone()[0] == 1
        assert {x[0] for x in db.execute("SELECT status FROM laporan")} == {"Dicocokkan"}

    # staf melihat kandidat; bukti wajib diisi
    assert "Dompet cokelat" in staf.c.get("/verifikasi/").get_data(as_text=True)
    r = staf.post("/verifikasi/1", {"hasil": "Disetujui", "bukti_kepemilikan": "x", "catatan": ""})
    assert "minimal 10 karakter" in r.get_data(as_text=True)
    r = staf.post("/verifikasi/1", {"hasil": "Disetujui", "catatan": "",
                                    "bukti_kepemilikan": "Menyebut isi dompet dan menunjukkan KTM yang sesuai"})
    assert r.status_code == 302
    with app.app_context():
        assert {x[0] for x in get_db().execute("SELECT status FROM laporan")} == {"Diverifikasi"}

    # keputusan tidak dapat diulang
    r = staf.post("/verifikasi/1", {"hasil": "Ditolak", "bukti_kepemilikan": "bukti lain yang panjang",
                                    "catatan": "tes"}, follow_redirects=True)
    assert "sudah diputuskan" in r.get_data(as_text=True)

    # penyerahan barang
    assert staf.post("/verifikasi/1/diambil", token_url="/verifikasi/1").status_code == 302
    with app.app_context():
        db = get_db()
        assert {x[0] for x in db.execute("SELECT status FROM laporan")} == {"Diambil"}
        assert db.execute("SELECT waktu_pengambilan FROM verifikasi").fetchone()[0] is not None
        assert db.execute("SELECT COUNT(*) FROM riwayat_status WHERE status='Diambil'").fetchone()[0] == 2

    # rekap untuk pimpinan
    html = pimpinan.c.get("/rekap/").get_data(as_text=True)
    assert "100.0%" in html
    csv = pimpinan.c.get("/rekap/riwayat.csv")
    assert csv.mimetype == "text/csv" and "Diambil" in csv.get_data(as_text=True)


def test_verifikasi_ditolak_mengembalikan_status(app, baru):
    kat, lok = id_kategori(app, "Kunci"), id_lokasi(app, "Parkiran Motor")
    a, b, staf = baru(), baru(), baru()
    a.login(*MHS); b.login(*MHS2); staf.login(*STAF)
    kirim_laporan(a, "Kehilangan", nama="Kunci motor", kat=kat, lok=lok, desk="Kunci motor gantungan beruang")
    kirim_laporan(b, "Temuan", nama="Kunci motor", kat=kat, lok=lok, desk="Kunci motor gantungan beruang pink")
    r = staf.post("/verifikasi/1", {"hasil": "Ditolak", "bukti_kepemilikan": "Tidak bisa menyebut ciri khas",
                                    "catatan": ""})
    assert "Catatan wajib" in r.get_data(as_text=True)
    staf.post("/verifikasi/1", {"hasil": "Ditolak", "bukti_kepemilikan": "Tidak bisa menyebut ciri khas",
                                "catatan": "Ciri tidak sesuai"})
    with app.app_context():
        db = get_db()
        assert {x[0] for x in db.execute("SELECT status FROM laporan")} == {"Dilaporkan"}
        assert db.execute("SELECT status_pencocokan FROM pencocokan").fetchone()[0] == "Ditolak"


def test_laporan_sendiri_tidak_dicocokkan(app, baru):
    kat, lok = id_kategori(app, "Elektronik"), id_lokasi(app, "Gedung A")
    a = baru()
    a.login(*MHS)
    kirim_laporan(a, "Kehilangan", nama="Earphone putih", kat=kat, lok=lok, desk="Earphone nirkabel putih")
    kirim_laporan(a, "Temuan", nama="Earphone putih", kat=kat, lok=lok, desk="Earphone nirkabel putih")
    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) FROM pencocokan").fetchone()[0] == 0


def test_izin_peran(app, baru):
    mhs, staf, pim = baru(), baru(), baru()
    mhs.login(*MHS); staf.login(*STAF); pim.login(*PIMPINAN)
    assert mhs.c.get("/verifikasi/").status_code == 403
    assert mhs.c.get("/rekap/").status_code == 403
    assert staf.c.get("/rekap/").status_code == 403
    assert pim.c.get("/laporan/baru").status_code == 403
    assert pim.c.get("/verifikasi/").status_code == 403
    assert mhs.post("/verifikasi/1/diambil", token_url="/cari").status_code == 403


def test_ciri_barang_temuan_disembunyikan(app, baru):
    kat, lok = id_kategori(app, "Dompet & Tas"), id_lokasi(app, "Kantin FILKOM")
    penemu, orang_lain, staf = baru(), baru(), baru()
    penemu.login(*MHS2); orang_lain.login(*MHS); staf.login(*STAF)
    kirim_laporan(penemu, "Temuan", nama="Dompet misterius", kat=kat, lok=lok,
                  desk="RAHASIA: ada foto kucing di dalam dompet")
    detail_lain = orang_lain.c.get("/laporan/1").get_data(as_text=True)
    assert "RAHASIA" not in detail_lain and "Kantin FILKOM" not in detail_lain and "disembunyikan" in detail_lain
    assert "RAHASIA" in staf.c.get("/laporan/1").get_data(as_text=True)
    assert "RAHASIA" in penemu.c.get("/laporan/1").get_data(as_text=True)
    # pencarian tidak boleh dipakai menebak isi deskripsi temuan
    assert "Dompet misterius" not in orang_lain.c.get("/cari?q=kucing").get_data(as_text=True)
    assert "Dompet misterius" in staf.c.get("/cari?q=kucing").get_data(as_text=True)


def test_unggah_foto_valid_dan_palsu(app, baru):
    k = baru()
    k.login(*MHS)
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 64
    r = kirim_laporan(k, "Kehilangan", foto=(io.BytesIO(png), "foto.png"))
    assert r.status_code == 302
    palsu = kirim_laporan(k, "Kehilangan", foto=(io.BytesIO(b"<?php echo 1;"), "backdoor.png"))
    assert "bukan gambar yang valid" in palsu.get_data(as_text=True)
    salah_ekstensi = kirim_laporan(k, "Kehilangan", foto=(io.BytesIO(b"abc"), "dok.exe"))
    assert "Format foto" in salah_ekstensi.get_data(as_text=True)
    with app.app_context():
        nama = get_db().execute("SELECT foto FROM laporan WHERE foto IS NOT NULL").fetchone()[0]
    assert k.c.get(f"/foto/{nama}").status_code == 200
    assert k.c.get("/foto/..%2Fconfig.py").status_code == 404


def test_pencarian_dan_filter(app, baru):
    kat, lok = id_kategori(app, "Kunci"), id_lokasi(app, "Parkiran Motor")
    k = baru()
    k.login(*MHS)
    kirim_laporan(k, "Kehilangan", nama="Kunci motor Honda", kat=kat, lok=lok, desk="Kunci motor Honda gantungan")
    html = k.c.get(f"/cari?q=honda&kategori={kat}").get_data(as_text=True)
    assert "Kunci motor Honda" in html
    assert "Tidak ada hasil" in k.c.get("/cari?q=tidakada").get_data(as_text=True)


def test_csv_mencegah_formula_injection(app, baru):
    pim, k = baru(), baru()
    k.login(*MHS); pim.login(*PIMPINAN)
    kirim_laporan(k, "Kehilangan", nama="=HYPERLINK(\"x\")", desk="Nama berbahaya untuk uji CSV")
    isi = pim.c.get("/rekap/riwayat.csv").get_data(as_text=True)
    assert "'=HYPERLINK" in isi


def test_header_keamanan(baru):
    r = baru().c.get("/login")
    assert r.headers["X-Frame-Options"] == "DENY" and "default-src 'self'" in r.headers["Content-Security-Policy"]
