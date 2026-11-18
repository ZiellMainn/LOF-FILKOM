import secrets
from functools import wraps

from flask import abort, g, redirect, request, session, url_for, flash


def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(24)
    return session["_csrf"]


def periksa_csrf():
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        kirim = request.form.get("_csrf", "")
        asli = session.get("_csrf", "")
        if not asli or not secrets.compare_digest(kirim, asli):
            abort(400, "Sesi formulir kedaluwarsa. Muat ulang halaman lalu coba lagi.")


def butuh_login(fn):
    @wraps(fn)
    def bungkus(*a, **kw):
        if g.get("user") is None:
            flash("Silakan masuk terlebih dahulu.", "info")
            return redirect(url_for("auth.login", next=request.full_path if request.method == "GET" else None))
        return fn(*a, **kw)
    return bungkus


def butuh_izin(izin):
    def dekorator(fn):
        @wraps(fn)
        @butuh_login
        def bungkus(*a, **kw):
            if not g.user.boleh(izin):
                abort(403)
            return fn(*a, **kw)
        return bungkus
    return dekorator


def url_aman(target):
    """Hanya izinkan redirect ke path internal (cegah open redirect)."""
    return bool(target) and target.startswith("/") and not target.startswith("//") and "\\" not in target
