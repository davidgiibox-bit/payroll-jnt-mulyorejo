# Panduan Deploy ke Render

Semua konfigurasi teknis sudah disiapkan (`render.yaml`, `gunicorn`, migrasi otomatis saat build).
Langkah di bawah ini perlu dilakukan David sendiri karena butuh akun Render & Google Cloud pribadi.

## 1. Siapkan kredensial Google Sheets (untuk Fase 2 — absensi)

1. Buka [Google Cloud Console](https://console.cloud.google.com/) → buat project baru (atau pakai yang sudah ada).
2. Aktifkan **Google Sheets API** untuk project tsb.
3. Buat **Service Account** (IAM & Admin → Service Accounts → Create).
4. Buat key baru untuk service account itu, format **JSON** — file ini akan ter-download.
5. Buka spreadsheet "Absensi Internal J&T Express" di Google Sheets → klik **Share** → tambahkan email service account (formatnya `nama@project-id.iam.gserviceaccount.com`) sebagai **Viewer**.
6. Catat **Spreadsheet ID** dari URL spreadsheet: `https://docs.google.com/spreadsheets/d/`**`INI_ID_NYA`**`/edit`.
7. Simpan isi file JSON tadi — akan dipakai di langkah 3 (env var `GOOGLE_SHEETS_CREDENTIALS_JSON_CONTENT`).

## 2. Push kode ke GitHub

Render deploy dari repo Git. Kalau belum ada repo:

```bash
git init
git add .
git commit -m "Initial commit - Payroll J&T Mulyorejo"
```

Buat repo baru di GitHub (bisa privat), lalu push:

```bash
git remote add origin <url-repo-github-anda>
git push -u origin main
```

## 3. Deploy di Render

1. Login ke [Render](https://render.com) (buat akun kalau belum ada).
2. Dashboard → **New** → **Blueprint** → hubungkan repo GitHub tadi. Render otomatis membaca `render.yaml` dan menyiapkan 2 resource: web service + PostgreSQL database.
3. Sebelum "Apply", isi env var yang ditandai `sync: false` di `render.yaml`:
   - `GOOGLE_SHEETS_CREDENTIALS_JSON_CONTENT` → paste seluruh isi file JSON dari langkah 1.
   - `GOOGLE_SHEETS_SPREADSHEET_ID` → ID spreadsheet dari langkah 1.
4. Klik **Apply**. Render akan build (`pip install` + `flask db upgrade` + `flask seed-menu`) lalu jalankan `gunicorn wsgi:app`.
5. Setelah deploy sukses, buat akun superadmin pertama lewat **Shell** tab di Render dashboard (web service → Shell):
   ```bash
   flask buat-superadmin --username <username> --password <password> --nama "Nama Anda"
   ```

## 4. Cek aplikasi jalan

Buka URL yang diberikan Render (mis. `https://payroll-jnt-mulyorejo.onrender.com`), login pakai akun superadmin di atas.

## 5. Upgrade ke tier berbayar (Starter) untuk produksi

Tier gratis Render: database expired 30 hari, web service sleep kalau idle — cocok untuk uji coba saja.
Untuk pemakaian tim sehari-hari:

1. Render Dashboard → database `payroll-jnt-db` → **Change Plan** → pilih **Basic 256MB** (~$6/bulan).
2. Render Dashboard → web service `payroll-jnt-mulyorejo` → **Change Plan** → pilih **Starter** (~$7/bulan).

Total ±$13/bulan (~Rp210rb), sesuai keputusan yang sudah disepakati.

## 6. Custom domain (opsional, nanti)

Render Dashboard → web service → **Settings** → **Custom Domain** — bisa ditambahkan kapan saja setelah David punya domain sendiri.

## Catatan penting

- **Setelah deploy**, jalankan proses payroll bulan berjalan lewat menu Payroll di web (bukan CLI) — sistem otomatis menarik data dari Google Sheets absensi memakai kredensial yang sudah diatur.
- Kalau kredensial Google Sheets salah/belum di-share ke service account, sistem akan menampilkan pesan error yang jelas di halaman Payroll (bukan crash) — tinggal cek ulang langkah 1.
- Ganti `SECRET_KEY` bila dirasa perlu lewat Render env var (Render sudah generate otomatis yang aman saat pertama deploy).
