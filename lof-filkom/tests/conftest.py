import re
import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from app.db import get_db, init_db  # noqa: E402
from app.seed import isi_data_demo  # noqa: E402
from app.services.auth_service import AuthService  # noqa: E402


@pytest.fixture()
def app(tmp_path):
    app = create_app({"DATABASE": str(tmp_path / "t.db"), "UPLOAD_DIR": str(tmp_path / "up"),
                      "TESTING": True, "SECRET_KEY": "tes"})
    with app.app_context():
        init_db()
        # master data saja; laporan dibuat oleh tes sendiri
        from app import seed
        db = get_db()
        asli = seed.LAPORAN[:]
        seed.LAPORAN.clear()
        isi_data_demo(db)
        seed.LAPORAN.extend(asli)
    AuthService.reset()
    return app


class Klien:
    def __init__(self, app):
        self.c = app.test_client()

    def token(self, url="/login"):
        html = self.c.get(url).get_data(as_text=True)
        m = re.search(r'name="_csrf" value="([^"]+)"', html)
        return m.group(1) if m else ""

    def login(self, nim, sandi):
        return self.c.post("/login", data={"nim_nip": nim, "kata_sandi": sandi, "_csrf": self.token()})

    def post(self, url, data=None, token_url=None, **kw):
        data = dict(data or {})
        data["_csrf"] = self.token(token_url or url)
        return self.c.post(url, data=data, **kw)


MHS = ("255150207111011", "mahasiswa123")
MHS2 = ("255150207111005", "mahasiswa123")
STAF = ("198001012005011001", "staf12345")
PIMPINAN = ("197501012000031001", "pimpinan123")


@pytest.fixture()
def baru(app):
    return lambda: Klien(app)
