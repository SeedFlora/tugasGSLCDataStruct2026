# Tugas Eksplorasi Struktur Data C dan Rust

Tugas ini dikerjakan dalam **kelompok berisi tepat tiga mahasiswa** selama **tujuh hari sejak diumumkan**. Tujuannya adalah menguji satu keputusan desain yang sering muncul dalam struktur data: kapan waktu yang dipakai untuk membuat indeks sepadan dengan pencarian yang lebih cepat dan memori tambahan. Tugas ini adalah latihan persiapan yang terpisah dari UTS individu.

## Data yang dipakai

Gunakan `data/hour_shuffled.csv` yang disediakan bersama tugas. Berkas ini berasal dari [`hour.csv` pada dataset Bike Sharing](https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset) oleh Hadi Fanaee-T, UCI Machine Learning Repository, 2013, DOI [10.24432/C5W894](https://doi.org/10.24432/C5W894), berlisensi [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Isinya **17.379 catatan peminjaman sepeda per jam** pada 2011–2012. Urutan baris diacak sekali dengan seed tetap; nilai setiap kolom tidak diubah. Gunakan salinan ini agar semua kelompok bekerja dengan input yang sama. Berikan atribusi tersebut bila berkas disertakan dalam ZIP hasil.

Satu catatan diidentifikasi oleh pasangan **tanggal `dteday` dan jam `hr`**. Pasangan ini unik pada berkas yang disediakan. Nilai yang dicari adalah `cnt`, jumlah peminjaman pada jam tersebut. Simpan sedikitnya kolom berikut dan jelaskan tipe yang dipilih:

| Kolom | Makna dan tipe logis | Pilihan representasi |
|---|---|---|
| `instant` | ID baris, bilangan bulat positif | `uint32_t` / `u32`; untuk pemeriksaan, bukan kunci pencarian |
| `dteday` | tanggal `YYYY-MM-DD` | ubah menjadi bilangan `YYYYMMDD` (`uint32_t` / `u32`) atau jelaskan pilihan lain |
| `hr` | jam 0–23 | `uint8_t` / `u8` |
| `cnt` | jumlah peminjaman, bilangan bulat tidak negatif | `uint32_t` / `u32` |
| `temp`, `hum` | suhu dan kelembapan ternormalisasi | `double` / `f64` |

Periksa jumlah baris, keunikan pasangan tanggal–jam, batas nilai jam, dan bahwa `cnt = casual + registered` saat membaca data. Catat bila parser menolak baris. `data/hour.csv` adalah salinan asli untuk memeriksa asal data; **benchmark memakai `hour_shuffled.csv`**. Halaman katalog UCI menampilkan jumlah instans yang sedikit berbeda; untuk tugas ini gunakan **17.379 baris data yang terverifikasi pada berkas `hour.csv`**.

Sebelum mulai, jalankan `python prepare_dataset.py --check` dari folder tugas ini (gunakan `python3` bila diperlukan). Perintah tersebut memeriksa hash berkas, keunikan kunci, dan jawaban pada semua kueri tanpa mengunduh ulang data. `data/manifest.json` mencatat sumber, transformasi, dan SHA-256 setiap berkas.

## Program yang dibuat

Buat kedua pendekatan berikut **dalam C dan Rust**. Keduanya harus memakai representasi catatan, aturan pembandingan kunci, dan berkas kueri yang setara.

1. **Scan:** simpan `n` catatan dalam array atau `Vec`, lalu cari pasangan tanggal–jam dengan memeriksa catatan satu per satu.
2. **Indeks terurut:** simpan catatan yang sama, lalu buat array tambahan berisi `(tanggal, jam, indeks baris)`. Urutkan array tambahan menurut tanggal lalu jam, dan gunakan binary search. Setelah kunci ditemukan, ambil `cnt` dari catatan asal.

Jalankan kedua pendekatan untuk `n = 5.000` dan `n = 15.000`, selalu memakai **`n` baris pertama** dari `hour_shuffled.csv`. Untuk setiap ukuran, pakai `data/queries_n5000.tsv` atau `data/queries_n15000.tsv`. Masing-masing berisi 2.000 kueri: 1.000 pasangan yang ada di `n` baris dan 1.000 pasangan asli dari baris yang tidak dimasukkan. Kolom `expected_cnt` berisi jawaban yang harus dikembalikan; `-1` berarti tidak ditemukan. **Periksa setiap jawaban**, bukan hanya jumlah kueri yang berhasil. Hasil C dan Rust harus sama.

## Pengukuran yang wajib dilaporkan

Jalankan C dengan optimisasi, misalnya `gcc -O2`, dan Rust dengan `cargo build --release`. Untuk setiap kombinasi bahasa, pendekatan, dan ukuran, lakukan **lima proses baru** pada mesin dan sistem operasi yang sama: total minimal **40 proses**. Variasikan urutan menjalankan C dan Rust. Catat CPU, RAM, sistem operasi, serta versi `gcc` dan `rustc`.

| Metrik | Aturan pengukuran |
|---|---|
| Waktu baca data | Waktu membaca dan mengubah CSV menjadi array catatan, dalam ms. Laporkan terpisah dari waktu indeks dan pencarian. |
| Waktu membangun indeks | Waktu membuat dan mengurutkan indeks setelah data dibaca, dalam ms. Untuk scan, tulis `0` karena tidak ada indeks tambahan. |
| Waktu pencarian | Muat kueri sebelum timer. Di dalam timer jangan membaca berkas, mencetak, atau memeriksa jawaban. Ulangi seluruh 2.000 kueri sampai waktu terukur sedikitnya 200 ms; pakai hasil dalam sebuah checksum yang dicetak setelah timer. Laporkan `ns/kueri` = waktu dibagi seluruh kueri yang dijalankan. |
| Memori proses | Ukur **puncak RSS** pada Linux/WSL, misalnya dengan `/usr/bin/time -v`, atau **Peak Working Set** pada Windows. Laporkan dalam KiB dan sebutkan alatnya. Jalankan tiap pendekatan dalam proses terpisah. Metrik ini mencakup seluruh proses, termasuk data, kueri, runtime, dan alokasi. |
| Muatan struktur | Laporkan `sizeof(Record)` / `size_of::<Record>()`, kapasitas array, ukuran entri indeks, dan perkiraan byte yang dialokasikan untuk catatan serta indeks. Jelaskan padding dan setiap alokasi dinamis yang tidak tercakup oleh `sizeof`. Ini **bukan** angka RAM proses. |

Untuk lima proses, laporkan median setiap metrik dan rentang minimum–maksimum. Simpan hasil mentahnya. Jangan menyebut C atau Rust “paling cepat” secara umum dari satu komputer dan satu dataset.

Gunakan satu baris hasil mentah per proses dengan sedikitnya kolom `n`, `bahasa`, `metode`, `ulangan`, `load_ms`, `build_ms`, `ns_per_kueri`, `peak_ram_kib`, `payload_bytes`, `batch_diulang`, dan `jawaban_benar`. Tuliskan `jawaban_benar=2000` hanya setelah seluruh kueri dasar lolos pemeriksaan.

## Analisis yang harus dijawab

1. Apakah semua kueri menghasilkan jawaban yang tepat pada kedua bahasa dan pendekatan? Tunjukkan bukti ringkas.
2. Berapa tambahan waktu membangun dan tambahan muatan memori indeks? Seberapa besar penurunan waktu per kueri yang diperoleh?
3. Perkirakan jumlah kueri saat biaya membuat indeks mulai terbayar: `Q* = T_bangun_indeks / (t_scan - t_cari_indeks)`, dengan `t` sebagai waktu pencarian per kueri. Samakan satuan terlebih dahulu. Jika penyebut nol atau negatif, jelaskan mengapa titik impas tidak ada pada hasil kalian.
4. Mengapa selisih puncak RAM proses dapat berbeda dari selisih ukuran catatan dan indeks? Jelaskan juga bagaimana pilihan tipe data atau padding memengaruhi hasil.
5. Faktor apa yang membatasi perbandingan C dan Rust pada pengukuran kalian?

## Pembagian kerja dan pengumpulan

Anggota pertama memimpin implementasi C, anggota kedua memimpin implementasi Rust, dan anggota ketiga memimpin pemeriksaan data, berkas kueri, serta rekap pengukuran. **Ketiganya wajib meninjau silang kode dan mampu menjelaskan kedua program.** Cantumkan kontribusi nyata masing-masing dalam laporan.

Kumpulkan satu ZIP per kelompok paling lambat **hari ketujuh pukul 23.59 waktu kelas** melalui LMS. Isinya: kode C dan Rust yang dapat dibangun, `README.md` berisi perintah menjalankan, CSV hasil mentah dan ringkasan, serta laporan PDF **maksimal empat halaman**. Laporan memuat tabel tipe data, satu tabel atau grafik waktu dan memori, jawaban analisis, spesifikasi mesin, sumber data, dan kontribusi anggota. Siapkan demonstrasi **maksimal lima menit** pada pertemuan berikutnya. Git boleh dipakai untuk kolaborasi, tetapi **push Git bukan syarat pengumpulan**.

Penilaian menekankan ketepatan jawaban, kejelasan pilihan tipe data, pengukuran yang dapat diulang, interpretasi waktu–memori, dan kontribusi ketiga anggota. Jangan memakai dataset, starter, parameter, atau kunci dari paket UTS untuk tugas ini.

## Rencana tujuh hari

| Hari | Target kelompok |
|---|---|
| 1 | Periksa dataset dan bagi peran; sepakati tipe data dan antarmuka pencarian. |
| 2–3 | Selesaikan dua pendekatan dalam C dan Rust. |
| 4 | Jalankan seluruh kueri dan perbaiki ketidakcocokan jawaban. |
| 5 | Ukur waktu serta puncak RAM dengan proses baru. |
| 6 | Hitung median, ukuran struktur, dan titik impas; tulis laporan. |
| 7 | Tinjau silang, ulangi pemeriksaan akhir, dan unggah ZIP. |
