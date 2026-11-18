from flask import Blueprint, Response, g, render_template, request

from ..container import layanan
from ..models import STATUS_LAPORAN
from ..security import butuh_izin

bp = Blueprint("rekap", __name__, url_prefix="/rekap")


def _filter():
    return {
        "status": request.args.get("status") if request.args.get("status") in STATUS_LAPORAN else None,
        "tipe": request.args.get("tipe") if request.args.get("tipe") in ("Kehilangan", "Temuan") else None,
        "dari": request.args.get("dari") or None,
        "sampai": request.args.get("sampai") or None,
    }


@bp.route("/")
@butuh_izin("rekap")
def index():
    return render_template("rekap.html", r=layanan().rekap.ringkasan(g.user))


@bp.route("/riwayat")
@butuh_izin("rekap")
def riwayat():
    f = _filter()
    return render_template("riwayat.html", data=layanan().rekap.riwayat_semua(g.user, **f), f=f,
                           status_list=STATUS_LAPORAN)


@bp.route("/riwayat.csv")
@butuh_izin("rekap")
def riwayat_csv():
    isi = layanan().rekap.ekspor_csv(g.user, **_filter())
    return Response(isi, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=riwayat-spbh.csv"})
