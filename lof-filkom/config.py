import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Konfigurasi aplikasi. Semua nilai dapat diganti lewat environment variable."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "ganti-di-produksi")
    DATABASE = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "instance", "spbh.db"))
    UPLOAD_DIR = os.environ.get("UPLOAD_DIR", os.path.join(BASE_DIR, "instance", "uploads"))
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024  # 4 MB per permintaan
    AMBANG_SKOR = float(os.environ.get("AMBANG_SKOR", "50"))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"
    TAMPILKAN_AKUN_DEMO = os.environ.get("TAMPILKAN_AKUN_DEMO", "1") == "1"
    LOGIN_MAKS_GAGAL = 5
    LOGIN_KUNCI_DETIK = 300
