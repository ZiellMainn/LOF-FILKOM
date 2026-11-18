from flask import Blueprint, g, redirect, render_template, url_for

from ..container import layanan
from ..security import butuh_login

bp = Blueprint("beranda", __name__)


@bp.route("/")
@butuh_login
def index():
    s = layanan()
    terbaru = s.laporan_repo.terbaru(6)
    milik = s.laporan_repo.milik_user(g.user.id_user) if g.user.boleh("status") else []
    ringkas = {"aktif": sum(1 for x in milik if not x.selesai),
               "cocok": sum(1 for x in milik if x.status == "Dicocokkan"),
               "selesai": sum(1 for x in milik if x.selesai)}
    menunggu = len(s.pencocokan_repo.daftar("Menunggu Verifikasi")) if g.user.boleh("verifikasi") else None
    if g.user.boleh("rekap") and not g.user.boleh("lapor"):
        return redirect(url_for("rekap.index"))
    return render_template("beranda.html", terbaru=terbaru, milik=milik[:4], ringkas=ringkas, menunggu=menunggu)
