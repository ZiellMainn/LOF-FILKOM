class PencocokanService:
    """PencocokOtomatis: menghitung skor terhadap laporan lawan dan menyimpan kandidat."""

    def __init__(self, reader, writer, riwayat, repo_pencocokan, strategi, ambang_skor):
        self.reader = reader
        self.writer = writer
        self.riwayat = riwayat
        self.repo = repo_pencocokan
        self.strategi = strategi          # IMatchingStrategy
        self.ambang_skor = ambang_skor

    def jalankan_matching(self, id_laporan: int, id_user: int) -> int:
        """Mengembalikan jumlah kandidat baru. Tidak melakukan commit (dipanggil dalam transaksi)."""
        laporan = self.reader.ambil(id_laporan)
        baru = 0
        status = {laporan.id_laporan: laporan.status}
        for lawan in self.reader.ambil_laporan_lawan(laporan):
            if lawan.id_user == laporan.id_user:
                continue  # laporan milik sendiri tidak dicocokkan
            skor = self.strategi.hitung_skor(laporan, lawan)
            if skor < self.ambang_skor:
                continue
            kehilangan, temuan = (laporan, lawan) if laporan.get_tipe() == "Kehilangan" else (lawan, laporan)
            if self.repo.simpan_kandidat(kehilangan.id_laporan, temuan.id_laporan, skor):
                baru += 1
            status.setdefault(lawan.id_laporan, lawan.status)
            for lap_id in (laporan.id_laporan, lawan.id_laporan):
                if status[lap_id] == "Dilaporkan":
                    self.writer.ubah_status(lap_id, "Dicocokkan")
                    self.riwayat.catat(lap_id, "Dicocokkan", id_user)
                    status[lap_id] = "Dicocokkan"
        return baru
