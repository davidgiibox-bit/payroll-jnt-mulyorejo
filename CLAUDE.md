# Sistem Penggajian J&T Express — MULYOREJO DP

Dokumen ini adalah ringkasan seluruh keputusan desain yang sudah disepakati antara David (pemilik outlet) dan Claude, hasil dari sesi perencanaan panjang. Baca ini sebagai konteks sebelum mulai membangun apa pun.

## Konteks bisnis
- David adalah pemilik/manajer outlet J&T Express (MULYOREJO DP, kode DP: SUB39A, SUB97, dll — multi drop point dalam satu naungan MULYOREJO173).
- Tim terdiri dari berbagai jabatan: PIC, HRD, Finance, Supervisor (SPV), Koordinator, Koor QC, Admin, Processing, Sprinter, Sprinter BC, Kurir Delivery, Kurir Pickup, Driver.
- Periode gaji: **bulanan**.
- Sistem ini menggantikan proses payroll manual berbasis Excel yang sudah berjalan (ada file referensi asli, formulanya dipakai sebagai acuan beberapa komponen).

## Prinsip desain yang konsisten dipakai di seluruh sistem
1. **Configurable, bukan hardcode** — jenis reward, jabatan yang kena PHL, master alasan Berita Acara, hak akses per jabatan: semua bisa diubah tim lewat halaman admin, tidak ditulis di kode.
2. **Percaya pada hasil akhir tim, bukan hitung ulang** — untuk potongan terlambat dan insentif, sistem tidak reimplementasi rumus rumit tim; cukup tarik/import nilai final yang sudah dihitung tim di template/sheet masing-masing.
3. **Snapshot per periode** — nilai master (gaji pokok, tunjangan, BPJS-TK) yang dipakai untuk menghitung gaji periode tertentu disimpan sebagai snapshot di slip gaji, sehingga perubahan master di kemudian hari TIDAK mengubah slip gaji yang sudah terbit.
4. **Minim penyimpanan data mentah** — sistem mengolah data dari sumber luar (Google Sheets absensi, sistem pickup resi) lalu menyimpan hasil ringkasannya saja, bukan data mentah dalam jumlah besar, supaya database tetap ramping.

---

## 1. Data Master

### Jabatan
- Nama jabatan, gaji pokok default.

### Karyawan
Field: status aktif/tidak aktif, tanggal join, tanggal resign, Kode DP, Nama, NIK Karyawan, Jabatan, NPWP, NIK KTP, Rekening Bank, Alamat NPWP, **Status Pajak** (TK/0, K/0, K/1, dst — untuk referensi walau PPh21 tidak dihitung sistem), Jenis kelamin, **limit deposit individual**, **potongan BPJS-TK individual** (nominal tetap per karyawan, bisa beda-beda, bukan satu angka global).

### Tunjangan Masa Kerja
- Tabel berjenjang berdasarkan rentang masa kerja (bukan berdasarkan tanggal berlaku/expiry — nominal per jenjang statis sampai diubah manual).
- Kenaikan tahunan ada, tapi nominalnya **di-set manual oleh tim** setiap kali (bukan formula otomatis). Perlu halaman admin untuk kelola tabel rentang + nominal.

### BPJS-TK
- Nominal tetap **per karyawan individual** (bukan global, bukan per jabatan), field di tabel Karyawan, statis sampai diubah manual.

### Deposit
- Default potongan bulanan: Rp 200.000 (bisa di-setting, global).
- Limit atas: **per karyawan** (field individual, override dari default).
- Perlu **saldo berjalan (running balance)** per karyawan — berhenti motong begitu limit tercapai.
- Karyawan resign dengan sisa deposit: tetap dilacak (mirip sheet "Karyawan Non Aktif (DEPOSIT)" di file referensi lama).

---

## 2. Absensi (sumber: Google Sheets)

- Spreadsheet: "Absensi Internal J&T Express". Sheet kehadiran bernama pola **"Rekap [Bulan] [Tahun]"** (mis. "Rekap Agustus 2026") — bertambah tiap bulan, pola nama **konsisten**, sistem harus bisa tentukan sheet aktif sesuai periode payroll berjalan (jangan hardcode nama sheet).
- Sheet keterlambatan: **"KeterlambatanLog"** — HANYA satu sheet ini (tidak per bulan), tapi data lama **otomatis terhapus setelah > 1 bulan**. Karena retensi > 1 bulan, sistem cukup tarik data ini **sekali di awal proses payroll bulanan** (tidak perlu sinkronisasi harian), tapi disarankan ada sinkronisasi berkala (mis. mingguan) sebagai jaga-jaga.
- **Tidak perlu sinkronisasi berkala tersimpan lokal** — sistem tarik langsung dari Google Sheets setiap kali payroll diproses.

### Kolom sheet "Rekap [Bulan] [Tahun]"
DP, Nama Karyawan, Jabatan, kolom Masuk/Keluar per tanggal, lalu kolom rekap: **Sakit, Izin, Alpha, Tidak Finger, Alpha + Tdk Finger, Cuti, Off**.
- "Tidak Finger" dihitung fraksional (0,5 poin per kejadian), sudah otomatis tergabung ke kolom **"Alpha + Tdk Finger"** — kolom inilah yang dipakai untuk hitung potongan kehadiran, bukan kolom "Alpha" sendirian.

### Kolom sheet "KeterlambatanLog"
Nama, Tanggal, Periode, MenitLabel, **Nominal** (sudah dihitung sistem absensi), **Dibalikkan** (kalau ada pengajuan penghapusan potongan), Keterangan.
- Tarif potongan terlambat (untuk referensi, dihitung sistem absensi bukan payroll): 1–10 menit = Rp10.000, 10–20 menit = Rp30.000, 20–120 menit = Rp50.000, >120 menit = dihitung sebagai "Tidak Finger" (bukan potongan terlambat lagi).
- Potongan terlambat final per baris = **Nominal − Dibalikkan**, dijumlah per karyawan per periode.

### Rumus potongan kehadiran (poin d)
```
Potongan Kehadiran = (GajiPokok + Tunjangan) / 25 × (Alpha+TdkFinger + Izin)
```
- **Sakit, Cuti, Dinas TIDAK dipotong** (dianggap tetap dibayar).
- **Alpha+TidakFinger dan Izin** yang mengurangi hari kerja efektif dan kena potongan.
- Formula asli dari file referensi: `((Gapok+Tunjangan)/25 × (JumlahKehadiran+Sakit+Cuti)) − (Gapok+Tunjangan)` — sudah dikonfirmasi logikanya sama dengan di atas.

---

## 3. Komponen upload template generik (potongan lainnya, BBM, PPh21, THR)

Poin (f), (j), (m), (o) — **format kolom sama**: NIK + nominal + keterangan. Bisa pakai **satu importer generik**, TAPI:
- **Menu upload harus terpisah per komponen** (menu sendiri untuk BBM, menu sendiri untuk PPh21, dst) — bukan 1 form dengan dropdown pilih tipe.
- Alasan pemisahan menu: **hak akses berbeda per tim** (role tertentu hanya boleh upload komponen tertentu) DAN **mengurangi risiko human error** (salah upload ke komponen lain).
- **PPh21 tetap upload template dari tim**, BUKAN dihitung otomatis oleh sistem (walau file referensi lama punya rumus PTKP/PKP/tarif progresif, itu format lama yang sudah tidak dipakai tim — sengaja diabaikan).

---

## 4. Insentif (poin g)

Ada **3 skema/sheet berbeda**, masing-masing untuk kelompok jabatan berbeda:
1. **Insentif BO DP** — SPV, Koor, Koor QC. Komponen: PKB Koor, PKB Koor QC, KPI SPV, Potongan, dikali **Grade** (mis. Grade B = 90% multiplier).
2. **Insentif Sprinter** — Sprinter, Admin, Koor BC. Komponen: PP_CASH (omset pickup, tiered %), PP_PM & DFOD, insentif delivery, PKB Koor BC & Admin, insentif COD Admin, insentif Cash PU, tambahan/potongan RM.
3. **Insentif Kurir** — berdasarkan data pendapatan pickup/delivery (PP_CASH intercity/outcity, total delivery, retur, tambahan berat paket). **Catatan: format Gaji Kurir sedang diseragamkan tim dengan format Gaji Karyawan** — kolom final acuan insentif kurir perlu di-revisit setelah proses itu selesai di sisi tim.

**Keputusan penting:** sistem **TIDAK menghitung ulang** rumus tiered/grade yang rumit ini. Sistem hanya **import 3 sheet bulanan**, ambil kolom **NIK + nilai final** ("Total Insentif setelah Grade" untuk BO DP, "Total Insentif" untuk Sprinter & Kurir).

---

## 5. Reward / Tambahan (poin h)

- **Master data jenis reward** — tabel CRUD, dikelola admin, bisa nambah/hapus jenis reward kapan saja (jumlahnya bisa berubah).
- Reward biasa: upload template NIK + jenis reward (dari master) + nominal.
- **Entertainment dengan tim**: tab/form khusus — karena **1 event melibatkan banyak karyawan sekaligus**. Input: total biaya event, pilih anggota tim yang terlibat, lalu **nominal per orang di-input MANUAL** (bukan dibagi rata otomatis — porsi bisa beda-beda per orang).

---

## 6. PHL — Pekerja Harian Lepas (poin k)

- Perusahaan bayar dulu biaya PHL, lalu **dibebankan sebagian ke karyawan tertentu** saat payroll.
- Tim upload **total biaya PHL** (bukan nominal final per karyawan) — sistem yang hitung porsinya:
```
Biaya per paket = Total biaya PHL ÷ Total paket yang dihandle
Potongan per karyawan = Biaya per paket × Jumlah resi yang dipickup karyawan tsb
```
- Berlaku hanya untuk **jabatan tertentu** (saat ini Sprinter & Kurir Pickup) — **configurable**, bisa berubah.
- **Data jumlah resi pickup per karyawan**: rencananya jadi **sistem terpisah** (database sendiri di server internal), BUKAN bagian dari database payroll ini. Sumber data mentahnya masih perlu dicek/dipastikan David. **Untuk sekarang, sistem payroll cukup terima angka final dari tim (manual)** — integrasi otomatis ke sistem pickup resi dibahas belakangan setelah sistem itu ada.

---

## 7. Berita Acara + Cicilan (poin i & l) — modul paling kompleks

### Alur inti
1. **2 template import**:
   - **Template dari pusat (konfirmasi)**: AWB (resi), Nilai Claim, Reason Claim, Status Bayar, dll — kolom persis seperti file resmi dari HQ J&T (Periode, Tahun, Jenis Ecommerce, AWB, Lokasi Tertagih, Nilai Claim, Mitra, Region, RM, Status Bayar, Keterangan, Reason Claim). **Belum ada assignment karyawan** saat data ini masuk.
   - **Template dari tim (prediksi)**: tim sudah tahu siapa yang salah sebelum data pusat turun. Kolom: AWB, **NIK Karyawan** (langsung ter-assign), Nominal, **Reason Claim**, Tanggal, Keterangan. Status otomatis jadi **"Prediksi"** dan langsung masuk potongan periode berjalan.
2. **Reason Claim** = **master database alasan** (dropdown dikelola admin, bisa nambah), BUKAN teks bebas — supaya konsisten untuk laporan.
3. **Pencocokan otomatis by AWB**: kalau AWB yang sudah ada prediksinya muncul lagi di data pusat → cek selisih nominal, tim putuskan penyesuaian. Kalau AWB dari pusat **tidak pernah ada prediksinya** → jadi kasus baru, perlu **assignment MANUAL** oleh tim ke karyawan yang bertanggung jawab.
4. **Assignment manual untuk sekarang** — auto-suggest dari data pickup/delivery internal (yang sama dengan kebutuhan PHL di atas) adalah pengembangan LANJUTAN, bukan untuk versi awal.
5. Status kasus: **Prediksi → Menunggu Konfirmasi Pusat → Final**.

### Review sebelum final (poin l)
- Setelah semua kasus Berita Acara periode berjalan diproses, sistem tampilkan **total potongan per karyawan**, **diurutkan dari nominal terbesar ke terkecil** — supaya tim gampang ambil keputusan. **Tidak ada batas nominal otomatis** yang memicu opsi cicilan.

### Cicilan
- Tim bisa pilih per kasus: potong langsung penuh, atau **cicil** (tim tentukan jumlah bulan, misal 3 atau 6 bulan — tidak baku).
- Tiap cicilan disimpan sebagai **entri terpisah dengan saldo berjalan sendiri** — kalau karyawan punya beberapa cicilan aktif sekaligus, **semuanya jalan paralel**, TIDAK digabung jadi satu.
- **Karyawan resign dengan cicilan belum lunas**: sisa cicilan dipotong dari **gaji terakhir + saldo deposit** yang tersisa.

---

## 8. Struktur Slip Gaji — pemisahan sebelum/sesudah THP

Ada baris subtotal **THP (Take Home Pay)** di slip gaji sebelum potongan tertentu dikurangkan lagi. Pengelompokan final:

**Sebelum THP:**
- (c) Potongan Deposit
- (e) Potongan Terlambat
- (f) Potongan Lainnya
- (m) Potongan PPh21
- (n) Potongan BPJS-TK

**Sesudah THP:**
- (h) Potongan dari reward/entertainment (jika ada)
- (i)/(l) Berita Acara + Cicilan
- (j) Potongan BBM
- (k) Potongan PHL

*(Catatan: pemisahan ini murni untuk kebutuhan tampilan/laporan slip gaji, BUKAN untuk basis perhitungan pajak — karena PPh21 tetap upload template dan BPJS-TK adalah nilai tetap, bukan dihitung dari basis gaji tertentu.)*

---

## 9. Role & Hak Akses

- **Role yang ada**: PIC, HRD, Finance, Supervisor, Koordinator, Admin, Processing, Sprinter, Kurir Delivery, Kurir Pickup — **semua bisa login**.
- Sprinter, Kurir Delivery, Kurir Pickup, Processing (level operasional) secara default **hanya bisa melihat absensi dan slip gaji milik sendiri**.
- **Hak akses TIDAK hardcode per role** — diatur lewat **matriks Jabatan × Menu** yang bisa disesuaikan sendiri oleh PIC/HRD lewat halaman admin.
- Setiap kombinasi Jabatan × Menu punya **3 level akses**: **Lihat saja / Edit / Approve**.
- Auth/login dibangun **custom di Flask** (bukan pakai layanan pihak ketiga seperti Firebase Auth atau Supabase Auth).

---

## 10. Infrastruktur

- **Sistem akan online**, database TIDAK di komputer David (beda dari dashboard monitoring sebelumnya yang jalan lokal di laptop dengan SQLite).
- David belum familiar hosting/server — perlu opsi paling mudah dikelola, dan tidak mau gratis (mau yang murah tapi online stabil).
- **Keputusan final: Render** (bukan Supabase/Firebase).
  - **Development**: tier gratis Render dulu (web service gratis + PostgreSQL gratis, meski database gratis expired 30 hari — tidak masalah untuk data uji coba).
  - **Produksi**: upgrade ke Render Starter — web $7/bulan + PostgreSQL Basic 256MB $6/bulan (~$13/bulan ≈ Rp210rb).
  - Database Basic 256MB **cukup**, karena desain sistem hanya simpan hasil olahan/ringkasan (bukan data mentah dalam jumlah besar — data pickup resi ada di sistem terpisah, absensi ditarik langsung tanpa disimpan histori mentah).
- **Alasan Render dipilih dibanding Supabase**: lebih murah (~Rp210rb vs ~Rp400rb/bulan Supabase Pro), meski trade-off-nya auth/login perlu dibangun manual di Flask (bukan masalah besar karena backend Flask custom memang sudah diperlukan untuk logic payroll yang kompleks).
- **Alasan bukan Firebase**: Firebase pakai NoSQL (Firestore) yang kurang cocok untuk data yang sangat relasional seperti sistem ini (karyawan ↔ jabatan ↔ berbagai potongan ↔ cicilan ↔ snapshot gaji).
- **Akses sistem**: via browser (desktop & HP), tidak perlu install aplikasi. UI harus **responsif untuk HP** karena Sprinter/Kurir di lapangan akan akses lewat browser HP mereka untuk lihat absensi & slip gaji sendiri.
- **Domain**: belum punya domain sendiri, pakai subdomain gratis dari Render dulu (mis. `payroll-mulyorejo.onrender.com`), custom domain bisa menyusul nanti.

---

## 11. Roadmap pengembangan yang disepakati

1. **Fondasi** — setup project Flask + PostgreSQL (dev di Render), Data Master (Karyawan, Jabatan, Tunjangan Masa Kerja, BPJS-TK, Deposit), sistem Login & Role/Akses.
2. **Perhitungan gaji inti** — koneksi Google Sheets Absensi, kalkulasi potongan kehadiran & terlambat, mesin proses payroll dasar + snapshot per periode.
3. **Komponen upload** — importer generik (BBM/PPh21/THR/Potongan Lainnya), import Insentif (3 sheet), Reward + entertainment, PHL (terima angka final).
4. **Berita Acara + Cicilan** — import 2 template (pusat & prediksi), pencocokan AWB, assignment manual, cicilan.
5. **Output & laporan** — slip gaji (dengan pemisahan sebelum/sesudah THP), dashboard status kelengkapan komponen per periode.
6. **Deploy produksi** — migrasi ke Render Starter, testing dengan tim.

## Hal yang masih terbuka / perlu diklarifikasi lebih lanjut saat development
- Sumber data mentah untuk jumlah resi pickup (PHL) — David masih perlu mengecek ini.
- Integrasi otomatis sistem pickup/delivery internal ↔ payroll (untuk PHL dan auto-suggest Berita Acara) — dibahas nanti setelah sistem pickup resi terpisah itu dibangun.
- Kolom final acuan Insentif Kurir — menunggu tim menyeragamkan format Gaji Kurir dengan Gaji Karyawan.

## Referensi desain visual
Sudah ada prototype HTML awal (dashboard, data karyawan, absensi, upload komponen, reward, berita acara, slip gaji, role & akses) sebagai gambaran layout dan alur navigasi — gunakan sebagai referensi tampilan, bukan spesifikasi final.
