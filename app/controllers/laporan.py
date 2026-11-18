import os

from flask import (Blueprint, abort, current_app, g, jsonify, redirect, render_template, request,
                   send_from_directory, url_for)

from ..container import layanan
from ..security import butuh_izin, butuh_login
from ..services.errors import ValidasiError

bp = Blueprint("laporan", __name__)

KOLOM_FORM = ("tipe_laporan", "nama_barang", "id_kategori", "id_lokasi", "waktu_kejadian", "deskripsi")


@bp.route("/laporan/baru", methods=["GET", "POST"])
@butuh_izin("lapor")
def baru():
    s = layanan()
    isi = {k: request.form.get(k, "") for k in KOLOM_FORM}
    if request.method == "GET":
        isi["tipe_laporan"] = request.args.get("tipe", "Kehilangan")
    errors = {}
    if request.method == "POST":
        try:
            hasil = s.laporan.buat_laporan(isi, g.user, request.files.get("foto"))
        except ValidasiError as e:
            errors = e.errors
        else:
            return redirect(url_for("laporan.konfirmasi", id_laporan=hasil["id_laporan"], kandidat=hasil["kandidat"]))
    return render_template("form_laporan.html", isi=isi, errors=errors,
                           kategori=s.master.daftar_kategori(), lokasi=s.master.daftar_lokasi())


@bp.route("/laporan/<int:id_laporan>/konfirmasi")
@butuh_izin("lapor")
def konfirmasi(id_laporan):
    laporan, _ = layanan().laporan.ambil_untuk(id_laporan, g.user)
    if laporan is None or not laporan.milik(g.user.id_user):
        abort(404)
    return render_template("konfirmasi.html", laporan=laporan, kandidat=request.args.get("kandidat", 0, type=int))


@bp.route("/laporan/<int:id_laporan>")
@butuh_login
def detail(id_laporan):
    s = layanan()
    laporan, penuh = s.laporan.ambil_untuk(id_laporan, g.user)
    if laporan is None:
        abort(404)
    kandidat = s.pencocokan_repo.by_laporan(id_laporan) if (laporan.milik(g.user.id_user) or g.user.boleh("lihat_detail")) else []
    return render_template("detail.html", laporan=laporan, penuh=penuh,
                           riwayat=s.riwayat.daftar(id_laporan), kandidat=kandidat)


@bp.route("/laporan/<int:id_laporan>/status.json")
@butuh_login
def status_json(id_laporan):
    """Dipakai halaman detail untuk memperbarui status secara berkala (FR-06)."""
    s = layanan()
    laporan, _ = s.laporan.ambil_untuk(id_laporan, g.user)
    if laporan is None:
        abort(404)
    return jsonify(status=laporan.status, tahap=laporan.tahap,
                   riwayat=len(s.riwayat.daftar(id_laporan)))


@bp.route("/status")
@butuh_izin("status")
def status_saya():
    return render_template("status_saya.html", daftar=layanan().laporan_repo.milik_user(g.user.id_user))


@bp.route("/foto/<nama>")
@butuh_login
def foto(nama):
    aman = os.path.basename(nama)
    if aman != nama or not layanan().laporan.ambil_foto_untuk(aman, g.user):
        abort(404)
    return send_from_directory(current_app.config["UPLOAD_DIR"], aman)
