# tugasGSLCDataStruct2026

Tugas eksplorasi struktur data untuk **kelompok tiga mahasiswa**, dikerjakan selama **tujuh hari**. Baca [instruksi lengkap](TUGAS.md), lalu kerjakan perbandingan scan dan indeks terurut dalam C dan Rust pada data peminjaman sepeda per jam. Tugas ini terpisah dari UTS individu.

## Mulai

1. Siapkan compiler C 64-bit, Rust stable, dan Python 3.
2. Periksa paket data tanpa mengunduh ulang: `python prepare_dataset.py --check` (atau `python3` pada Linux/macOS).
3. Gunakan `data/hour_shuffled.csv` dan dua berkas kueri di `data/` sesuai [TUGAS.md](TUGAS.md). Simpan hasil kerja kelompok di folder sendiri.

## Sumber data

Data berasal dari **Hadi Fanaee-T, Bike Sharing, UCI Machine Learning Repository (2013)**, DOI [10.24432/C5W894](https://doi.org/10.24432/C5W894). [Halaman dataset](https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset) menyatakan lisensi [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). `data/hour.csv` adalah salinan asli dari arsip UCI. `data/hour_shuffled.csv` hanya mengubah urutan baris dan menormalkan akhir baris; berkas kueri dibuat dari catatan yang dimasukkan dan ditahan. Detail sumber, seed, dan SHA-256 ada di [manifest](data/manifest.json).

Repositori ini berisi tugas dan data latihan; soal, starter, serta kunci UTS tidak disertakan.
