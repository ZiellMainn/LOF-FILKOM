"""Filter Jinja untuk tampilan tanggal, status, dan skor."""
from datetime import datetime

BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


def _dt(teks):
    return datetime.strptime(str(teks)[:19], "%Y-%m-%d %H:%M:%S")


def tanggal(teks, dengan_jam=True):
    if not teks:
        return "-"
    d = _dt(teks)
    s = f"{d.day} {BULAN[d.month - 1]} {d.year}"
    return f"{s}, {d:%H:%M}" if dengan_jam else s


def waktu_relatif(teks):
    if not teks:
        return "-"
    selisih = datetime.now() - _dt(teks)
    detik = int(selisih.total_seconds())
    if detik < 60:
        return "baru saja"
    if detik < 3600:
        return f"{detik // 60} menit lalu"
    if detik < 86400:
        return f"{detik // 3600} jam lalu"
    if detik < 86400 * 7:
        return f"{detik // 86400} hari lalu"
    return tanggal(teks, False)


def kelas_status(status):
    return {"Dilaporkan": "s-lapor", "Dicocokkan": "s-cocok", "Diverifikasi": "s-verif",
            "Diambil": "s-ambil", "Menunggu Verifikasi": "s-cocok", "Disetujui": "s-ambil",
            "Ditolak": "s-tolak"}.get(status, "s-lapor")


def daftar_filter(app):
    app.jinja_env.filters.update(tanggal=tanggal, relatif=waktu_relatif, kelas_status=kelas_status)
    app.jinja_env.globals["TAHAP"] = ("Dilaporkan", "Dicocokkan", "Diverifikasi", "Diambil")
