from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for

from ..container import layanan
from ..security import url_aman
from ..services.errors import KredensialError

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("beranda.index"))
    galat = None
    if request.method == "POST":
        try:
            pengguna = layanan().auth.login(request.form.get("nim_nip", ""), request.form.get("kata_sandi", ""))
        except KredensialError as e:
            galat = str(e)
        else:
            session.clear()           # cegah session fixation
            session["id_user"] = pengguna.id_user
            tujuan = request.args.get("next", "")
            return redirect(tujuan if url_aman(tujuan) else url_for("beranda.index"))
    return render_template("login.html", galat=galat, nim_nip=request.form.get("nim_nip", ""))


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Anda sudah keluar.", "info")
    return redirect(url_for("auth.login"))
