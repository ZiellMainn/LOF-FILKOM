import os

from flask import Flask, g, render_template, session

from config import Config
from . import db as database
from .container import layanan
from .security import csrf_token, periksa_csrf


def create_app(config=None):
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(Config)
    if config:
        app.config.update(config)
    os.makedirs(os.path.dirname(app.config["DATABASE"]), exist_ok=True)
    os.makedirs(app.config["UPLOAD_DIR"], exist_ok=True)

    database.register(app)

    @app.before_request
    def muat_pengguna():
        g.user = None
        id_user = session.get("id_user")
        if id_user:
            g.user = layanan().pengguna.ambil(id_user)
            if g.user is None:
                session.clear()
        periksa_csrf()

    @app.after_request
    def header_keamanan(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "same-origin")
        resp.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; frame-ancestors 'none'")
        return resp

    @app.context_processor
    def konteks():
        return {"csrf_token": csrf_token, "pengguna": g.get("user")}

    from .controllers import auth, laporan, pencarian, verifikasi, rekap, beranda
    for modul in (auth, beranda, laporan, pencarian, verifikasi, rekap):
        app.register_blueprint(modul.bp)

    from .tampilan import daftar_filter
    daftar_filter(app)

    for kode, judul, pesan in (
        (400, "Permintaan tidak valid", "Sesi formulir kedaluwarsa atau data tidak sesuai. Muat ulang halaman lalu coba lagi."),
        (403, "Akses ditolak", "Peran akun Anda tidak memiliki izin untuk halaman ini."),
        (404, "Halaman tidak ditemukan", "Alamat yang Anda tuju tidak ada atau sudah dipindahkan."),
        (413, "Berkas terlalu besar", "Ukuran unggahan melebihi batas 4 MB."),
    ):
        app.register_error_handler(kode, lambda e, k=kode, j=judul, p=pesan: (
            render_template("galat.html", kode=k, judul=j, pesan=p), k))
    return app
