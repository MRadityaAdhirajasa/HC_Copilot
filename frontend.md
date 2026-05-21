Berikut adalah draf terstruktur untuk **`frontend.md`**. Dokumen ini dirancang khusus agar GitHub Copilot dapat membangun antarmuka Streamlit yang bersih, scannable, dan menggunakan palet warna yang Mas inginkan (dominan biru muda dan putih).

Silakan buat file baru bernama `frontend.md` di folder root proyek Anda dan masukkan konten berikut:

```markdown
# Frontend UI Planning: Candidate Scoring Dashboard

Dokumen ini mendefinisikan layout, alur interaksi pengguna (UX), serta panduan visual untuk antarmuka aplikasi Streamlit.

## 1. Visual Identity & Theme (Biru Muda & Putih)

Streamlit secara default menggunakan tema bawaan, namun kita akan mengarahkannya menggunakan konfigurasi `.streamlit/config.toml` dan injeksi CSS kustom ringan agar mendapatkan estetika profesional bernuansa korporat (clean, biru muda, dan putih).

### Panduan Palet Warna:
- **Primary Color:** `#4A90E2` atau `#A5D8FF` (Biru Muda / Sky Blue untuk tombol utama, tab, dan aksen)
- **Background Color:** `#FFFFFF` (Putih Bersih untuk area konten utama)
- **Secondary Background:** `#F0F4F8` (Biru Sangat Muda / Soft Gray-Blue untuk sidebar dan kartu informasi)
- **Text Color:** `#1C2A38` (Gelap/Navy untuk kontras teks yang tajam di atas latar putih)

---

## 2. Page Layout & Structure

Antarmuka akan dibagi menjadi 3 bagian utama: **Sidebar (Kontrol Admin)**, **Hero Metrics (Rangkuman Visual)**, dan **Main Data Table (Daftar & Aksi)**.

### A. Sidebar (Section Kiri - Background `#F0F4F8`)
*   **Logo & App Title:** Judul aplikasi "HC Talent Analytics".
*   **Data Ingestion Hub:** 
    *   Komponen `st.file_uploader` untuk menerima file CSV (10 data pelamar dummy dari Google Form).
    *   Tombol `"Seed Database"` (Aksen Biru Muda) untuk memasukkan data CSV ke Supabase.
*   **Configuration Preview:** Dropdown lipat (*expander*) untuk mengintip isi teks `Job Description` dan `Office Culture` yang digunakan sebagai acuan AI.

### B. Header & Hero Metrics (Top Content - Background `#FFFFFF`)
*   **Main Title:** "Candidate Interview Feedback Tracker".
*   **Status Cards (`st.columns`):** 3 buah metrik visual di bagian atas untuk merangkum kondisi database saat ini:
    *   **Total Pelamar** (Angka Besar)
    *   **Sudah Dinilai** (Angka dengan warna hijau/biru)
    *   **Belum Dinilai / Pending** (Angka dengan warna kuning/abu-abu)

### C. Main Dashboard Area (Central Content)
Menggunakan sistem **Tab Components** (`st.tabs`) untuk memisahkan data mentah dan data hasil penilaian:

1.  **Tab 1: 📊 Evaluation Dashboard (Utama)**
    *   Menampilkan tabel interaktif berisi daftar kandidat yang datanya sudah dievaluasi oleh AI.
    *   **Status Badge:** Menggunakan format warna kustom untuk kolom status:
        *   `Strong Hire` ➔ Latar belakang hijau muda / teks hijau tua.
        *   `Hire` ➔ Latar belakang biru muda / teks biru tua.
        *   `No Go` ➔ Latar belakang merah muda / teks merah tua.
    *   **Detail Viewer:** Jika baris kandidat diklik (atau dipilih via dropdown), tampilkan komponen *Card* putih yang memuat `Summary Reason` dari Gemini API secara lengkap beserta skor detailnya.

2.  **Tab 2: 📥 Pending Screening & Action**
    *   Menampilkan daftar pelamar yang statusnya masih `Pending` (baru diunggah dari CSV dan belum diproses AI).
    *   **The Action Button:** Sebuah tombol utama bertuliskan `"Run AI Assessment Engine"` (Warna Biru Muda Dominan). Ketika diklik, aplikasi akan menjalankan fungsi backend untuk memproses semua kandidat `Pending` satu per satu menggunakan Gemini API dengan animasi *loading* (`st.spinner`).

---

## 3. Component Mapping (Streamlit Syntax Guidance for Copilot)

Pastikan Copilot menggunakan komponen-komponen Streamlit berikut agar UI tetap modern:
- `st.set_page_config(layout="wide")` wajib diletakkan di baris paling atas `app.py` untuk memanfaatkan ruang layar horizontal secara maksimal.
- `st.dataframe` atau `st.data_editor` untuk menampilkan data Supabase agar kolomnya bisa diurutkan (*sortable*) dan dicari (*searchable*) oleh user HC.
- `st.metric` untuk menampilkan ringkasan angka di bagian atas.
- `st.toast` atau `st.success` untuk memberikan notifikasi visual instan setelah proses upload CSV atau penilaian AI selesai.

---

## 🚨 GIT & COPILOT DEV REMINDER
*Instruksi untuk Developer saat masuk fase frontend:*
- Mintalah Copilot untuk membuat layout-nya terlebih dahulu menggunakan data tiruan lokal (hardcoded list) sebelum menyambungkannya secara penuh ke fungsi pembaca Supabase di `backend.md`. Ini memastikan UI tidak patah di tengah jalan.
- Begitu tampilan dasar visual (layout sidebar, tab, dan tabel kosong) sudah muncul di browser Developer dengan skema warna biru-putih yang sesuai, segera kunci progresnya ke GitHub:
  ```bash
  git add frontend.md app.py
  git commit -m "style: frontend UI layout with blue-white theme implemented"
  git push origin main

```

```

---

Sekarang ketiga pilar perencanaan proyek Mas sudah lengkap:
1. `plan.md` (Kompas arah proyek & pengingat Git)
2. `backend.md` (Arsitektur data Supabase & Prompt Gemini)
3. `frontend.md` (Layout UI Streamlit & Estetika Biru-Putih)

Semua file ini bertindak sebagai "memori eksternal" yang sangat kuat untuk GitHub Copilot. Ketika Mas memulai *vibe coding* di file `app.py`, Mas cukup memberikan perintah awal seperti ini di Copilot Chat:

> *"Buka dan baca file plan.md, backend.md, dan frontend.md yang ada di root folder ini. Berdasarkan spesifikasi tersebut, buatkan struktur kode awal untuk file app.py."*

Apakah semua perencanaan ini sudah sesuai dengan ekspektasi Mas, atau ada modul spesifik yang ingin Mas ubah sebelum mulai menembakkan prompt pertama ke Copilot?

```