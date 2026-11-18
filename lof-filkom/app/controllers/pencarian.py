from flask import Blueprint, g, render_template, request

from ..container import layanan
from ..models import STATUS_LAPORAN
from ..security import butuh_izin

bp = Blueprint("pencarian", __name__)


@bp.route("/cari")
@butuh_izin("cari")
def cari():
    s = layanan()
    f = {
        "q": request.args.get("q", "").strip()[:100] or None,
        "id_kategori": request.args.get("kategori", type=int),
        "id_lokasi": request.args.get("lokasi", type=int),
        "tipe": request.args.get("tipe") if request.args.get("tipe") in ("Kehilangan", "Temuan") else None,
        "status": request.args.get("status") if request.args.get("status") in STATUS_LAPORAN else None,
    }
    hasil = s.laporan.cari(g.user, **f)
    return render_template("cari.html", hasil=hasil, f=f, kategori=s.master.daftar_kategori(),
                           lokasi=s.master.daftar_lokasi(), status_list=STATUS_LAPORAN,
                           ada_filter=any(v for v in f.values()))
