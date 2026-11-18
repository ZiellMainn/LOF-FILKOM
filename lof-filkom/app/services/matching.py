"""Strategi pencocokan berbasis aturan (rule-based). Skor 0-100 dari empat kriteria."""
import re
from datetime import datetime

from ..repositories.interfaces import IMatchingStrategy

FORMAT_WAKTU = "%Y-%m-%d %H:%M:%S"


def _token(teks: str) -> set:
    return {t for t in re.findall(r"[a-z0-9]+", (teks or "").lower()) if len(t) >= 3}


def _waktu(teks: str) -> datetime:
    return datetime.strptime(teks[:19], FORMAT_WAKTU)


class RuleBasedMatching(IMatchingStrategy):
    BOBOT_KATEGORI = 40
    BOBOT_LOKASI = 25
    BOBOT_WAKTU = 20
    BOBOT_TEKS = 15

    def hitung_skor(self, a, b) -> float:
        skor = 0.0
        if a.id_kategori == b.id_kategori:
            skor += self.BOBOT_KATEGORI
        if a.id_lokasi == b.id_lokasi:
            skor += self.BOBOT_LOKASI
        elif a.jenis_lokasi and a.jenis_lokasi == b.jenis_lokasi:
            skor += self.BOBOT_LOKASI * 0.4
        skor += self._skor_waktu(a.waktu_kejadian, b.waktu_kejadian)
        skor += self._skor_teks(a, b)
        return round(min(skor, 100.0), 2)

    def _skor_waktu(self, wa, wb) -> float:
        selisih = abs((_waktu(wa) - _waktu(wb)).total_seconds()) / 86400
        for batas, nilai in ((1, 1.0), (3, 0.75), (7, 0.5), (14, 0.25)):
            if selisih <= batas:
                return self.BOBOT_WAKTU * nilai
        return 0.0

    def _skor_teks(self, a, b) -> float:
        ta = _token(f"{a.nama_barang} {a.deskripsi or ''}")
        tb = _token(f"{b.nama_barang} {b.deskripsi or ''}")
        if not ta or not tb:
            return 0.0
        irisan = len(ta & tb) / min(len(ta), len(tb))
        return self.BOBOT_TEKS * min(1.0, irisan * 2)
