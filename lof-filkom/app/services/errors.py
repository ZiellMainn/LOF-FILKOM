class ValidasiError(Exception):
    """Data masukan tidak valid. `errors` berisi pesan per kolom."""

    def __init__(self, errors: dict):
        super().__init__("Data tidak valid")
        self.errors = errors


class AturanError(Exception):
    """Pelanggaran aturan bisnis (mis. status tidak mengizinkan)."""


class KredensialError(Exception):
    pass


class DitolakError(Exception):
    """Pengguna tidak berhak melakukan aksi."""
