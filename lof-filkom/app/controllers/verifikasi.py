from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from ..container import layanan
from ..security import butuh_izin
from ..services.errors import AturanError, ValidasiError

bp = Blueprint("verifikasi", __name__, url_prefix="/verifikasi")


@bp.route("/")
@butuh_izin("verifikasi")
def daftar():
    tampil = request.args.get("tampil", "menunggu")
    status = {"menunggu": "Menunggu Verifikasi", "disetujui": "Disetujui", "ditolak": "Ditolak"}.get(tampil)
    return render_template("verifikasi_daftar.html", kandidat=layanan().verifikasi.ambil_kandidat(g.user, status),
                           tampil=tampil)


@bp.route("/<int:id_pencocokan>", methods=["GET", "POST"])
@butuh_izin("verifikasi")
def periksa(id_pencocokan):
    s = layanan().verifikasi
    errors, isi = {}, {k: request.form.get(k, "") for k in ("hasil", "bukti_kepemilikan", "catatan")}
    if request.method == "POST":
        try:
            s.verifikasi_klaim(id_pencocokan, isi["hasil"], isi["bukti_kepemilikan"], isi["catatan"], g.user)
        except ValidasiError as e:
            errors = e.errors
        except AturanError as e:
            flash(str(e), "error")
            return redirect(url_for("verifikasi.periksa", id_pencocokan=id_pencocokan))
        else:
            flash("Keputusan verifikasi disimpan.", "ok")
            return redirect(url_for("verifikasi.periksa", id_pencocokan=id_pencocokan))
    p, v = s.ambil_detail(g.user, id_pencocokan)
    if p is None:
        abort(404)
    return render_template("verifikasi_form.html", p=p, v=v, errors=errors, isi=isi)


@bp.route("/<int:id_pencocokan>/diambil", methods=["POST"])
@butuh_izin("verifikasi")
def diambil(id_pencocokan):
    try:
        layanan().verifikasi.tandai_diambil(id_pencocokan, g.user)
        flash("Barang ditandai sudah diambil pemiliknya. Kasus selesai.", "ok")
    except AturanError as e:
        flash(str(e), "error")
    return redirect(url_for("verifikasi.periksa", id_pencocokan=id_pencocokan))
