<<<<<<< HEAD
# Project Plan: Automated Candidate Interview Feedback Tracker

## 1. Project Overview
Aplikasi ini adalah sebuah dashboard demonstrasi untuk tim Human Capital (HC) yang berfungsi otomatis menilai, memberi skor, dan menentukan status kelulusan awal para pelamar kerja (role: Software Engineer). 

Aplikasi mengekstrak data mentah kandidat dari Google Form (via CSV), mengirimkannya ke LLM (Gemini API) untuk dianalisis berdasarkan kecocokan Kualifikasi Pekerjaan (*Job Description*) dan Budaya Perusahaan (*Office Culture*), lalu menyimpannya ke database cloud untuk ditampilkan dalam dashboard interaktif.

## 2. Project Goals
- **Otomasi Screening:** Mengurangi waktu evaluasi awal berkas pelamar secara signifikan menggunakan AI.
- **Standarisasi Penilaian:** Menghasilkan metrik skor objektif (Skor Teknis & Budaya) yang konsisten untuk setiap kandidat.
- **Penyimpanan Terpusat:** Migrasi dari pengelolaan data berbasis *spreadsheet* manual ke sistem *database* relasional cloud yang terstruktur.

## 3. Minimum Viable Product (MVP) Scope
Untuk kebutuhan demo, fitur dibatasi pada fungsi inti berikut:
- **Data Seeding & Upload:** Halaman/tombol khusus untuk mengunggah file CSV berisi 10 data pelamar dummy untuk dimasukkan ke database.
- **AI Scoring Engine:** Integrasi Gemini Free Tier API untuk mengevaluasi data pelamar secara *on-demand* (sekali klik) dan mengembalikan output berformat JSON.
- **HC Dashboard Monitoring:** Tabel utama yang menampilkan daftar pelamar, visualisasi skor, ringkasan alasan dari AI, serta status otomatis (`Strong Hire`, `Hire`, `No Go`).
- **Cloud Connection:** Aplikasi lokal terhubung langsung secara *live* dengan Supabase DB dan siap dideploy ke Streamlit Community Cloud.

## 4. Tech Stack
- **Frontend & App Framework:** Streamlit (Python)
- **Database:** Supabase (PostgreSQL free tier)
- **AI Engine:** Google AI Studio (Gemini SDK - Free Tier)
- **Deployment:** Streamlit Community Cloud

---

## 🚨 IMPORTANT: GIT WORKFLOW & CO-PILOT REMINDER
*Catatan untuk Pengembang (Mas): Sebelum masuk ke fase penulisan kode, pastikan lingkungan Git Anda sudah siap.*

1. **Initialize & Connect Repository:**
   ```bash
   git init
   git remote add origin <URL_REPOSITORY_GITHUB_MAS>
   git branch -M main
