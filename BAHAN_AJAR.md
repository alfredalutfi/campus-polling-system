# 📘 Bahan Ajar Kelompok — Campus Polling System

> Dokumen ini dibuat supaya **semua anggota kelompok paham** apa yang dibangun, **kenapa** dibangun begitu,
> dan **bisa menjawab pertanyaan dosen** saat demo. Baca berurutan sekali, lalu pakai Bagian 7–10 sebagai contekan saat latihan.

**Daftar isi**
0. [Cara Menjalankan Proyek (Langkah demi Langkah)](#0-cara-menjalankan-proyek-langkah-demi-langkah)
1. [Gambaran Besar (1 menit paham)](#1-gambaran-besar-1-menit-paham)
2. [Peta File: Siapa Mengerjakan Apa](#2-peta-file-siapa-mengerjakan-apa)
3. [Konsep Inti yang Wajib Dikuasai](#3-konsep-inti-yang-wajib-dikuasai)
4. [Bedah Kode per File](#4-bedah-kode-per-file)
5. [Perjalanan Satu Klik "Kirim Suara"](#5-perjalanan-satu-klik-kirim-suara)
6. [Perjalanan Satu `git push`](#6-perjalanan-satu-git-push)
7. [Naskah Demo 5–8 Menit](#7-naskah-demo-58-menit)
8. [Bank Soal: Pertanyaan Dosen + Jawaban](#8-bank-soal-pertanyaan-dosen--jawaban)
9. [Troubleshooting](#9-troubleshooting)
10. [Cheat Sheet Perintah & Checklist H-1](#10-cheat-sheet-perintah--checklist-h-1)

---

## 0. Cara Menjalankan Proyek (Langkah demi Langkah)

Ada 3 tahap. **Tahap A** cukup untuk melihat aplikasinya jalan. **Tahap B & C** dikerjakan **sekali saja** oleh satu orang (laptop yang dipakai demo). **Tahap D** adalah urutan menyalakan semuanya di hari demo.

### Prasyarat (install dulu)
| Software | Wajib? | Cek dengan |
|---|---|---|
| **Docker Desktop** (Mac/Windows) atau Docker Engine (Linux) | Wajib | `docker --version` dan `docker compose version` |
| **Git** | Wajib | `git --version` |
| **Python 3** | Opsional (untuk unit test tanpa Docker) | `python3 --version` |
| **ngrok** + akun gratis di ngrok.com | Wajib untuk webhook | `ngrok version` |

> **Pengguna Windows:** jalankan semua perintah di terminal **WSL2 (Ubuntu)**, bukan CMD/PowerShell. Skrip `.sh` dan path `$HOME` di Jenkins mengandalkan shell Linux.

### Tahap A — Menjalankan aplikasi di laptop (±3 menit)

1. **Nyalakan Docker Desktop**, tunggu sampai statusnya *Running*. Cek: `docker info` (tidak boleh error).
2. **Masuk ke folder proyek**:
   ```bash
   cd ~/Documents/"cc naufal"/campus-polling-system   # laptop yang sekarang
   # anggota lain setelah clone:  cd campus-polling-system
   ```
3. **Build & jalankan** seluruh stack:
   ```bash
   docker compose up -d --build
   ```
   Yang terjadi: image backend di-build, network `app-net` & volume `polling-db-data` dibuat, lalu 2 kontainer dinyalakan.
4. **Cek status**:
   ```bash
   docker compose ps
   ```
   `polling-backend` harus **`(healthy)`** dan `polling-frontend` **`Up`**.
5. **Buka browser:** **http://localhost:8080** → pojok kanan atas harus **API Online** (titik hijau).
6. **Coba-coba** (opsional):
   ```bash
   ./scripts/test-api.sh          # demo semua endpoint + error
   ./scripts/data-immunity.sh     # demo data tetap ada walau kontainer dihapus
   ```
7. **Mematikan / menyalakan lagi**:
   ```bash
   docker compose down            # matikan (data suara TETAP aman di volume)
   docker compose up -d           # nyalakan lagi (tanpa --build kalau kode backend tidak berubah)
   ```
   ⚠️ Jangan pakai `docker compose down -v` kecuali memang ingin **menghapus semua data suara**.

> Kalau mengubah `app.py` → wajib `docker compose up -d --build`.
> Kalau mengubah `index.html` → cukup refresh browser (bind mount).

### Tahap B — Upload ke GitHub (sekali saja)

1. Buat repository baru di GitHub bernama `campus-polling-system` (**kosong**, jangan centang "Add README").
2. Buat **Personal Access Token (classic)**: GitHub → foto profil → **Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token (classic)**
   - Note: `Jenkins CI/CD UTS Token`, Expiration: 30/90 hari
   - Centang **`repo`** dan **`admin:repo_hook`** → **Generate token** → **salin & simpan** token `ghp_...` (hanya ditampilkan sekali!)
3. Push kode dari folder proyek:
   ```bash
   git init -b main
   git add .
   git commit -m "Campus Polling System - initial commit"
   git remote add origin https://github.com/alfredalutfi/campus-polling-system.git
   git push -u origin main
   ```
   Saat diminta *password*, tempel **token PAT** (bukan password akun GitHub).
4. Tambahkan anggota lain: repo → **Settings → Collaborators → Add people**.

### Tahap C — Setup Jenkins + Webhook (sekali saja)

**C1. Nyalakan Jenkins**
```bash
cd jenkins
docker compose up -d --build        # build pertama ±3–10 menit (download image Jenkins)
docker exec jenkins cat $HOME/jenkins_home/secrets/initialAdminPassword   # salin password awal
cd ..
```
Buka **http://localhost:9090** → tempel password → **Install suggested plugins** → buat user admin → Save and Finish.

**C2. Simpan token GitHub di Jenkins**
**Manage Jenkins → Credentials → System → Global credentials → Add Credentials**
- Kind: **Username with password**
- Username: *username GitHub* · Password: *token PAT `ghp_...`*
- ID: `github-pat` → **Create**

**C3. Buat Pipeline Job**
**+ New Item** → nama `campus-polling-system` → pilih **Pipeline** → OK
- General: ✅ **GitHub project** → Project url: `https://github.com/alfredalutfi/campus-polling-system/`
- Triggers: ✅ **GitHub hook trigger for GITScm polling**
- Pipeline → Definition: **Pipeline script from SCM**
  - SCM: **Git** · Repository URL: `https://github.com/alfredalutfi/campus-polling-system.git`
  - Credentials: **github-pat** · Branch Specifier: `*/main` · Script Path: `Jenkinsfile`
- **Save**

**C4. Build pertama (manual)**
Klik **Build Now** → buka build `#1` → **Console Output** / **Stage View**. Kelima stage harus **hijau**. Akhir log: `DEPLOY SUKSES`.

**C5. Buka tunnel publik dengan ngrok** (biarkan terminal ini tetap terbuka)
```bash
ngrok config add-authtoken <authtoken-dari-dashboard-ngrok>   # sekali saja
ngrok http 9090
```
Salin URL `https://xxxx.ngrok-free.app` dari baris **Forwarding**.

**C6. Pasang Webhook di GitHub**
Repo → **Settings → Webhooks → Add webhook**
- Payload URL: `https://xxxx.ngrok-free.app/github-webhook/` ← **wajib ada `/` di akhir**
- Content type: `application/json` · Event: **Just the push event** → **Add webhook**
- Cek tab **Recent Deliveries** → harus ada centang hijau / status **200**.

**C7. Tes CI/CD otomatis**
```bash
# ubah sesuatu, misal POLL_QUESTION di docker-compose.yml
git add . && git commit -m "test webhook" && git push
```
Di Jenkins, build baru muncul **sendiri** dalam beberapa detik dengan keterangan *"Started by GitHub push"*. 🎉

### Tahap D — Urutan menyalakan di hari demo
1. Nyalakan **Docker Desktop** → kontainer aplikasi & Jenkins otomatis ikut menyala (`restart: unless-stopped`). Cek: `docker ps`.
   Kalau belum: `cd jenkins && docker compose up -d && cd ..`
2. **Wajib:** jalankan `docker compose up -d` dari **root folder proyek lokal**, walaupun kontainer sudah jalan.
   Alasannya: setelah Jenkins men-deploy, bind mount frontend menunjuk ke folder workspace Jenkins. Perintah ini mengembalikannya ke folder lokal supaya demo Bind Mount (edit `index.html` di VS Code) berhasil.
3. Jalankan **`ngrok http 9090`**. Kalau URL-nya **berubah**, update *Payload URL* webhook di GitHub (C6).
4. Cek: http://localhost:8080 → **API Online**, http://localhost:9090 → Jenkins bisa login.
5. Reset data demo: `curl -X DELETE "http://localhost:8080/api/votes?index=all"`
6. Ikuti **Naskah Demo** di [Bagian 7](#7-naskah-demo-58-menit) (persiapan lengkap ada di 7.2).

---

## 1. Gambaran Besar (1 menit paham)

Bayangkan **pemilu di kampus**:

| Dunia nyata | Di proyek kita |
|---|---|
| Kertas suara & bilik tempat mencoblos | **Frontend** (`index.html`) — halaman web tempat mahasiswa memilih |
| Petugas KPPS yang menerima & menghitung suara | **Backend** (`app.py`) — REST API yang memvalidasi & menghitung suara |
| Kotak suara yang disegel | **Named Volume** `polling-db-data` — tempat `votes.json` disimpan, aman walau petugas diganti |
| Lorong khusus antara bilik & meja petugas | **Custom Bridge Network** `app-net` — jalur komunikasi privat antar-kontainer |
| Resepsionis di pintu masuk | **Nginx** — melayani halaman web & meneruskan permintaan `/api` ke backend |
| SOP penyelenggaraan pemilu tertulis | **docker-compose.yml** — semua aturan infrastruktur ditulis di 1 file |
| Panitia otomatis yang memeriksa & memasang ulang TPS setiap ada perubahan aturan | **Jenkins** — CI/CD pipeline yang otomatis jalan setiap `git push` |

**Inti tugas ini bukan coding-nya**, tapi membuktikan 4 hal:
1. Aplikasi berjalan di **kontainer** yang terisolasi.
2. Data **tidak hilang** walau kontainer dihapus (**Data Immunity**).
3. Frontend & backend berkomunikasi lewat **nama service** di network sendiri.
4. Setiap `git push` → **otomatis** dicek, di-build, di-deploy, dan dicek kesehatannya oleh Jenkins.

---

## 2. Peta File: Siapa Mengerjakan Apa

Pembagian penguasaan materi (setiap orang tetap wajib paham garis besar semuanya):

| Anggota | Pegang file | Wajib bisa jelaskan | Tampil di demo | Bobot rubrik |
|---|---|---|---|---|
| **Aizza Kamelia Insani** (101012300341) | `backend/app.py`, `tests/test_app.py`, `backend/Dockerfile` | Endpoint, status code 200/201/400/404/409, penyimpanan JSON, Named Volume & Data Immunity | Adegan 4, 6, 8 (±2 mnt 20 dtk) | Backend 20% + Storage |
| **Alfreda Luthfi Hermana** (101012300406) | `frontend/index.html`, `nginx/default.conf`, `docker-compose.yml` | `fetch()`, auto-refresh, reverse proxy `/api`, Bind Mount, network `app-net`, DNS Docker | Adegan 2, 3, 5 (±2 mnt 45 dtk) | Frontend 15% + Docker 25% |
| **Bagus Tegar Panutan** (101012330193) | `Jenkinsfile`, `jenkins/*`, `README.md` | 5 stage pipeline, webhook, PAT, ngrok, docker.sock | Adegan 1, 7 (±2 mnt 45 dtk) | Jenkins 25% + Dokumentasi 15% |

---

## 3. Konsep Inti yang Wajib Dikuasai

### 3.1 Image vs Container
- **Image** = cetakan / resep yang **read-only** (contoh: `campus-polling-backend:latest`, `nginx:1.27-alpine`).
- **Container** = **instance yang sedang berjalan** dari image. Satu image bisa jadi banyak container.
- Analogi: image = **file installer**, container = **aplikasi yang sedang dibuka**.
- Container itu **sekali pakai (ephemeral)**: kalau dihapus, semua yang ditulis di dalamnya ikut hilang — **kecuali** ditulis ke volume.

### 3.2 Dockerfile
File berisi langkah-langkah membuat image. Di proyek ini (`backend/Dockerfile`):

| Instruksi | Artinya |
|---|---|
| `FROM python:3.12-slim` | Mulai dari image Python resmi versi ringan |
| `ENV ...` | Set environment variable (port, folder data) |
| `WORKDIR /app` | Folder kerja di dalam kontainer |
| `RUN useradd ... appuser` | Buat user non-root → lebih aman |
| `COPY app.py .` | Salin kode ke dalam image |
| `USER appuser` | Jalankan aplikasi sebagai user non-root |
| `VOLUME ["/var/lib/polling_data"]` | Tandai folder ini untuk data persisten |
| `EXPOSE 5000` | Dokumentasi bahwa app mendengarkan port 5000 (tidak membuka port ke host) |
| `HEALTHCHECK ...` | Docker mengecek `/health` tiap 10 detik → status `(healthy)` |
| `CMD ["python", "app.py"]` | Perintah yang dijalankan saat kontainer start |

### 3.3 Named Volume vs Bind Mount ⭐ (25% nilai — pasti ditanya!)

| | **Named Volume** | **Bind Mount** |
|---|---|---|
| Dipakai untuk | **Backend** → `votes.json` | **Frontend** → `index.html` & config Nginx |
| Ditulis di compose | `polling-db-data:/var/lib/polling_data` | `./frontend:/usr/share/nginx/html:ro` |
| Lokasi data | Dikelola Docker (`/var/lib/docker/volumes/...`) | Folder di laptop kita (path host) |
| Tujuan | **Data persisten**, aman, portabel, tidak tergantung struktur folder host | **Development**: edit file di laptop → langsung terlihat di kontainer |
| Kalau kontainer dihapus | Data **tetap ada** ✅ | File tetap ada (memang di laptop) |

**Kenapa database (votes.json) TIDAK pakai bind mount?** Rubrik menyebut itu kesalahan (“DB pakai Bind Mount” = nilai Cukup).
Alasannya: data jadi tergantung path folder di laptop tertentu, rawan masalah permission antar-OS, mudah terhapus/teredit tidak sengaja, dan tidak portabel. Named volume dikelola penuh oleh Docker dan dirancang untuk data aplikasi.

**Kenapa frontend pakai bind mount?** Supaya UI bisa diubah tanpa rebuild image — cocok untuk file statis yang sering diedit.

> `:ro` = **read-only**. Nginx hanya perlu membaca file, jadi kontainer tidak bisa mengubah file di laptop kita.

### 3.4 Custom Bridge Network & DNS Docker
- Docker punya network default `bridge`, tapi di network default **kontainer tidak bisa saling panggil pakai nama**.
- Di **custom bridge network** (`app-net`), Docker menyediakan **DNS internal** (alamat `127.0.0.11`).
  Jadi Nginx cukup memanggil `http://backend:5000` — `backend` adalah **nama service** di compose.
- Keuntungan: **IP kontainer boleh berubah** (misal setelah dihapus & dibuat ulang) — nama tetap sama.
- **Isolasi**: port 5000 backend **tidak dipublish** ke laptop. Satu-satunya pintu masuk adalah Nginx di port 8080.
  Coba: `curl http://localhost:5000/votes` dari laptop → gagal. Itu **disengaja**.

### 3.5 Docker Compose
- Menuliskan seluruh infrastruktur (service, volume, network, port, env) secara **deklaratif** di `docker-compose.yml`.
- **Deklaratif** = kita menulis *kondisi akhir yang diinginkan*, Docker yang mengatur caranya.
  Kebalikannya **imperatif** = mengetik `docker run ...` panjang satu per satu.
- `docker compose up -d` aman dijalankan berulang kali: hanya kontainer yang berubah yang dibuat ulang (**idempotent**).
- `depends_on: condition: service_healthy` → frontend baru dinyalakan setelah backend **sehat**.
- `name: campus-polling` → nama project dikunci supaya Jenkins & laptop mengelola stack yang sama.

### 3.6 Nginx sebagai Reverse Proxy
- Browser hanya bicara ke **satu alamat**: `http://localhost:8080`.
  - `/` → Nginx kirim `index.html`.
  - `/api/votes` → Nginx **teruskan** ke `http://backend:5000/votes` (prefix `/api` dibuang dengan `rewrite`).
- Keuntungan: tidak perlu CORS, backend tetap tersembunyi, cukup 1 port terbuka.
- Trik `resolver 127.0.0.11 valid=10s` + variabel `$backend_upstream`: Nginx **me-resolve ulang** nama `backend` secara berkala.
  Tanpa ini, setelah backend dibuat ulang (IP baru), Nginx masih menyimpan IP lama → error 502.
- Kalau backend mati, Nginx menjawab JSON `503` yang rapi (bukan halaman error HTML).

### 3.7 REST API & HTTP Status Code (20% nilai)

| Kode | Arti | Kapan muncul di app kita |
|---|---|---|
| **200 OK** | Berhasil | GET /votes, DELETE berhasil |
| **201 Created** | Data baru dibuat | POST /votes berhasil |
| **400 Bad Request** | Input klien salah | JSON rusak, `option` bukan A/B, `voter` kosong, `index` bukan angka |
| **404 Not Found** | Tidak ditemukan | `index` di luar jangkauan, endpoint tidak dikenal |
| **405 Method Not Allowed** | Method salah | `PUT /votes` |
| **409 Conflict** | Bentrok dengan data yang ada | Pemilih yang sama vote 2× |
| **413 Payload Too Large** | Body > 10 KB | Kirim body raksasa |
| **500 Internal Server Error** | Bug di server | Ditangkap → server tidak crash |
| **503 Service Unavailable** | Layanan tidak tersedia | Dari Nginx saat kontainer backend mati |

Aturan sederhana: **4xx = salah klien**, **5xx = salah server**.

### 3.8 CI/CD
- **CI (Continuous Integration)**: setiap perubahan kode **otomatis dicek** (syntax, unit test) → bug ketahuan cepat.
- **CD (Continuous Deployment)**: kode yang lolos **otomatis di-deploy** ke server.
- Tanpa CI/CD: SSH ke server, `git pull`, build, restart manual → lambat & rawan lupa langkah.

### 3.9 Jenkins, Jenkinsfile, Webhook, PAT
- **Jenkins**: server otomasi yang menjalankan pipeline.
- **Jenkinsfile (Declarative Pipeline)**: definisi pipeline sebagai kode, disimpan di repo (**Pipeline as Code**) → ikut ter-versioning di Git.
- **GitHub Webhook**: GitHub **memberi tahu** Jenkins (HTTP POST ke `/github-webhook/`) setiap ada push. Lawannya *polling* (Jenkins yang bertanya terus-menerus) → boros.
- **ngrok**: Jenkins kita di `localhost` tidak bisa dijangkau GitHub dari internet. ngrok membuat URL publik sementara yang diteruskan ke `localhost:9090`.
- **PAT (Personal Access Token)**: “password khusus” untuk Jenkins mengakses GitHub, dengan izin terbatas (`repo`, `admin:repo_hook`) dan masa berlaku. Lebih aman dari password asli: bisa dicabut kapan saja tanpa ganti password akun.
- **docker.sock**: Jenkins (di dalam kontainer) memakai Docker milik laptop lewat file socket `/var/run/docker.sock` (pola *Docker-outside-of-Docker*).

---

## 4. Bedah Kode per File

### 4.1 `backend/app.py` (Aizza)
Struktur dari atas ke bawah:

1. **Konfigurasi** — `PORT`, `DATA_DIR`, `POLL_QUESTION`, `OPTION_A/B` dibaca dari environment variable → bisa diubah dari compose tanpa ubah kode.
2. **Storage layer**
   - `load_votes()` → baca `votes.json`. Jika file belum ada → `[]`. Jika rusak → di-backup jadi `.corrupt-...` lalu mulai dari kosong.
   - `save_votes()` → **penulisan atomik**: tulis ke file sementara lalu `os.replace()`. Kalau kontainer mati di tengah penulisan, file lama tetap utuh.
   - `_lock = threading.Lock()` → server melayani request **paralel** (`ThreadingHTTPServer`); lock mencegah dua vote bersamaan saling menimpa file.
3. **`summarize()`** → hitung jumlah A & B, persen, dan pemenang (`A`, `B`, `SERI`, atau `null`).
4. **`PollingHandler`** (turunan `BaseHTTPRequestHandler`)
   - `do_GET/do_POST/do_DELETE` → semua masuk ke `_dispatch()` yang mencocokkan `(method, path)` dengan tabel `routes`.
   - Semua error validasi dilempar sebagai `ApiError(status, pesan)` dan ditangkap di **satu tempat** → respons JSON `{"error": ..., "status": ...}` yang konsisten.
   - Error tak terduga → 500, tapi **server tidak crash**.
5. **Format `votes.json`** di dalam volume:
   ```json
   [
     { "voter": "Budi - 1301220001", "option": "A", "timestamp": "2026-11-10T08:40:36+00:00" }
   ]
   ```
   `index` = posisi dalam list (0, 1, 2, …). Setelah item dihapus, index item sesudahnya **bergeser** — itu wajar untuk API berbasis index sesuai soal.

**Kenapa tanpa Flask?** Ketentuan soal: "Python tanpa framework berat". Kita memakai `http.server` bawaan Python → image kecil, tanpa `pip install`.

**Unit test** (`tests/test_app.py`): 15 test, menyalakan server di port acak dengan folder data sementara, lalu menguji setiap endpoint & setiap kode error. Jenkins menjalankannya di stage *Syntax Check*.

### 4.2 `frontend/index.html` (Alfreda)
- Hanya HTML + CSS + **Vanilla JS** (tanpa React/Vue/jQuery, tanpa CDN).
- Fungsi `api(path, options)` membungkus `fetch()`: kirim request → parse JSON → kalau status bukan 2xx, lempar error berisi pesan dari backend → ditampilkan sebagai **toast** merah.
- `loadVotes()` → `GET /api/votes` → update kartu A/B, bar persentase, tabel.
- Form submit → `POST /api/votes` → muat ulang data.
- Tombol **Hapus** & **Reset Semua** → `DELETE /api/votes?index=X` / `?index=all`, dengan konfirmasi 2× klik (tanpa `confirm()` bawaan browser).
- **Auto-refresh tiap 5 detik** (`setInterval`) → kalau teman vote dari HP lain, layar ikut ter-update (memenuhi “tombol Delete berfungsi real-time” & “tidak perlu refresh manual”).
- **Keamanan XSS**: nama pemilih ditampilkan dengan `textContent`, **bukan** `innerHTML`, jadi input seperti `<script>` tidak dieksekusi.
- Indikator **API Online/Offline** di pojok kanan atas.

### 4.3 `nginx/default.conf` (Alfreda)
- `location /` → file statis, header `Cache-Control: no-store` supaya perubahan langsung terlihat.
- `location /api/` → `rewrite` membuang prefix `/api`, `proxy_pass` ke `backend:5000`.
- `listen 80` **dan** `listen [::]:80` → melayani IPv4 & IPv6.
- `error_page 502 503 504` → JSON 503 saat backend mati.

### 4.4 `docker-compose.yml` (Alfreda)
Hafalkan 3 bagian:
```yaml
services:     # 2 kontainer: backend & frontend
volumes:      # polling-db-data  -> Named Volume (nama dikunci, tanpa prefix)
networks:     # app-net, driver bridge
```
Hal penting:
- Backend: `build: ./backend` + `image: campus-polling-backend:latest`, volume `polling-db-data:/var/lib/polling_data`, **tanpa `ports`** (hanya `expose`).
- Frontend: image resmi `nginx:1.27-alpine`, `ports: "8080:80"` (format **host:kontainer**), bind mount `./frontend` & `./nginx`.
- Folder `./nginx` di-mount sebagai **folder**, bukan file tunggal. Alasannya: `git pull` mengganti file dengan file baru (inode baru); bind mount file tunggal akan tetap menunjuk file lama.

### 4.5 `Jenkinsfile` (Bagus)
```
triggers { githubPush() }        ← dipicu webhook GitHub
Checkout              → checkout scm, tampilkan commit terakhir
Syntax Check          → py_compile, 15 unit test, docker compose config, cek index.html
Build Image           → docker build -t campus-polling-backend:<BUILD_NUMBER> -t ...:latest
Automated Deployment  → docker compose up -d --remove-orphans, nginx -s reload
Health Check          → docker exec polling-frontend wget http://127.0.0.1/api/health (retry 15×)
post { always { docker image prune -f } }
```
- **Kenapa Health Check lewat kontainer frontend?** Satu request itu sekaligus membuktikan: Nginx hidup → proxy jalan → DNS `backend` di `app-net` jalan → backend sehat. Juga tidak tergantung Jenkins berjalan di mana.
- **Kenapa tag image pakai `BUILD_NUMBER`?** Supaya setiap versi tercatat & bisa **rollback** ke versi sebelumnya.
- `disableConcurrentBuilds()` → dua push beruntun tidak deploy bersamaan.
- Kalau satu stage gagal (merah), stage berikutnya **tidak dijalankan** → kode rusak tidak pernah ter-deploy.

### 4.6 `jenkins/` (Bagus)
- `Dockerfile`: Jenkins LTS + Docker CLI + Buildx + Compose + Python3 + plugin (`workflow-aggregator`, `git`, `github`, …).
- `docker-compose.yml`: Jenkins di **port 9090** (8080 sudah dipakai aplikasi), mount `docker.sock`, dan `JENKINS_HOME=${HOME}/jenkins_home` dengan **path identik di host & kontainer**.
  Kenapa? Saat pipeline menjalankan `docker compose up`, bind mount `./frontend` dibaca oleh Docker **di laptop** memakai path workspace Jenkins. Kalau path-nya beda, Docker me-mount folder kosong → Nginx 403/500.

---

## 5. Perjalanan Satu Klik "Kirim Suara"

```
[Browser]  klik "Kirim Suara"
   │  fetch('/api/votes', {method:'POST', body:'{"voter":"Budi","option":"A"}'})
   ▼
[Laptop :8080] ──port mapping 8080→80──►  [polling-frontend / Nginx]
   │  location /api/  →  rewrite /api/votes → /votes
   │  resolver 127.0.0.11: "backend" = 172.23.0.2  (DNS Docker di app-net)
   ▼
[polling-backend :5000]  app.py → _dispatch → handle_post_votes
   │  validasi JSON, option A/B, voter tidak kosong, belum pernah vote
   │  lock → load_votes() → append → save_votes() (atomik)
   ▼
[/var/lib/polling_data/votes.json]  ← ini sebenarnya Named Volume polling-db-data
   │
   ◄── 201 Created {"message": "...", "results": {...}}
[Browser] toast hijau + loadVotes() → kartu & tabel ter-update
```

---

## 6. Perjalanan Satu `git push`

```
git push origin main
   ▼
GitHub ──Webhook POST──► https://xxxx.ngrok-free.app/github-webhook/ ──► Jenkins :9090
   ▼
Jenkins: job "campus-polling-system" (Pipeline script from SCM, branch main)
   1 Checkout  →  2 Syntax Check  →  3 Build Image  →  4 Automated Deployment  →  5 Health Check
   ▼                                                    │
 (gagal di mana pun = merah, deploy dibatalkan)          ▼
                                     docker compose up -d → kontainer yang berubah dibuat ulang
                                     Named Volume TIDAK disentuh → suara lama tetap ada
```

---

## 7. Naskah Demo 5–8 Menit

Rubrik meminta video **5–8 menit** yang memperlihatkan: **(1) demo UI & API**, **(2) simulasi Data Immunity** (hapus kontainer backend), dan **(3) simulasi CI/CD** (git push → Jenkins ter-trigger otomatis). Naskah di bawah memenuhi ketiganya dalam 8 adegan.

### 7.1 Gambaran alur demo

| # | Adegan | Pembicara | Durasi | Membuktikan rubrik |
|---|---|---|---|---|
| 1 | Pembukaan & arsitektur | Bagus | 0:00–0:45 | Dokumentasi (15%) |
| 2 | Infrastruktur Docker | Alfreda | 0:45–1:45 | Docker & Storage (25%) |
| 3 | Demo UI | Alfreda | 1:45–3:00 | Frontend (15%) |
| 4 | Demo API & error handling | Aizza | 3:00–3:50 | Backend API (20%) |
| 5 | Bind Mount | Alfreda | 3:50–4:20 | Docker & Storage (25%) |
| 6 | Data Immunity | Aizza | 4:20–5:20 | Docker & Storage (25%) |
| 7 | CI/CD git push → Jenkins | Bagus | 5:20–7:20 | Jenkins CI/CD (25%) |
| 8 | Penutup | Aizza | 7:20–7:50 | – |

> ⚠️ **Urutan Adegan 5 (Bind Mount) harus SEBELUM Adegan 7 (CI/CD).** Setelah Jenkins men-deploy, bind mount frontend menunjuk ke folder **workspace Jenkins** (`~/jenkins_home/workspace/...`), bukan folder proyek di laptop. Jadi mengedit `index.html` di VS Code tidak akan terlihat lagi sampai kamu menjalankan `docker compose up -d` dari folder proyek.

### 7.2 Persiapan (30 menit sebelum rekam — tidak direkam)

**a. Nyalakan semua layanan**
```bash
# 1. Docker Desktop sudah Running, lalu dari ROOT folder proyek:
cd ~/Documents/"cc naufal"/campus-polling-system
git pull                              # pastikan kode lokal = kode di GitHub
docker compose up -d --build          # WAJIB dari folder ini (bind mount -> folder lokal)
docker compose ps                     # backend (healthy), frontend Up

# 2. Jenkins
cd jenkins && docker compose up -d && cd ..

# 3. ngrok (di terminal terpisah, biarkan terbuka)
ngrok http 9090
```

**b. Cek webhook masih tersambung**
- Kalau URL ngrok berubah → GitHub repo → Settings → Webhooks → Edit → ganti Payload URL → Update.
- Klik webhook → tab **Recent Deliveries** → klik **Redeliver** pada delivery terakhir → harus **200**.

**c. Bersihkan data & tampilan**
```bash
curl -X DELETE "http://localhost:8080/api/votes?index=all"
clear
```

**d. Siapkan layar** (urutan tab/jendela)
1. **Browser tab 1:** halaman GitHub repo (README dengan diagram)
2. **Browser tab 2:** `http://localhost:8080` (aplikasi)
3. **Browser tab 3:** `http://localhost:9090/job/campus-polling-system/` (Jenkins, sudah login)
4. **Browser tab 4:** GitHub → Settings → Webhooks (opsional, untuk bukti)
5. **Terminal** di root proyek — perbesar font (Cmd/Ctrl `+`) supaya terbaca di video
6. **VS Code** membuka folder proyek

**e. Lain-lain**
- Matikan notifikasi (Mac: Focus / Do Not Disturb; Windows: Focus assist).
- Zoom browser 110–125% supaya teks terbaca.
- Siapkan nama-nama pemilih contoh di catatan (misal `Budi - 1301220001`, `Sari - 1301220002`, `Andi - 1301220003`).
- Latihan minimal **1× penuh** sambil pakai stopwatch.

---

### 7.3 Langkah demi langkah

#### 🎬 Adegan 1 — Pembukaan & arsitektur (Bagus, ±45 detik)
**Layar:** Browser tab 1 (README di GitHub), scroll ke diagram arsitektur.

**Ucapkan:**
> "Assalamualaikum / Selamat pagi. Kami kelompok … dengan anggota Aizza Kamelia Insani, Alfreda Luthfi Hermana, dan Bagus Tegar Panutan. Kami memilih studi kasus 7, **Sistem Polling Kampus**, aplikasi pemungutan suara Opsi A vs Opsi B.
> Arsitekturnya terdiri dari **dua kontainer**: frontend Nginx dan backend Python, yang terhubung lewat **custom bridge network `app-net`**. Data suara disimpan di **named volume `polling-db-data`**, sedangkan file frontend memakai **bind mount**. Semua didefinisikan di **docker-compose.yml**, dan setiap `git push` ke branch main otomatis memicu **Jenkins** lewat **GitHub Webhook** untuk menjalankan 5 stage pipeline."

---

#### 🎬 Adegan 2 — Infrastruktur Docker (Alfreda, ±1 menit)
**Layar:** VS Code (`docker-compose.yml`) → Terminal.

**Langkah:**
1. Di VS Code, buka `docker-compose.yml`. Tunjuk dengan kursor bagian `services`, `volumes: polling-db-data`, `networks: app-net`.
2. Di terminal, ketik satu per satu:
   ```bash
   docker compose ps
   ```
   👉 Tunjuk kolom **PORTS**: frontend `0.0.0.0:8080->80/tcp`, backend hanya `5000/tcp` (**tidak dipublish ke host**).
   ```bash
   docker network inspect app-net --format '{{range .Containers}}{{.Name}} {{.IPv4Address}}{{"\n"}}{{end}}'
   ```
   👉 Kedua kontainer berada di network `app-net`.
   ```bash
   docker exec polling-frontend nslookup backend
   ```
   👉 Nama `backend` di-resolve ke IP kontainer backend → bukti **DNS Docker**.
   ```bash
   docker volume ls | grep polling
   ```

**Ucapkan:**
> "Backend sengaja tidak membuka port ke host, jadi terisolasi. Satu-satunya pintu masuk adalah Nginx di port 8080. Nginx memanggil backend pakai **nama service** `backend`, bukan IP, karena custom network punya DNS internal Docker."

---

#### 🎬 Adegan 3 — Demo UI (Alfreda, ±1 menit 15 detik)
**Layar:** Browser tab 2 (`localhost:8080`).

**Langkah:**
1. Tunjuk indikator **API Online** (hijau) di pojok kanan atas.
2. Tekan **F12** (DevTools) → tab **Network** → filter **Fetch/XHR**. Biarkan terbuka di samping/bawah.
3. Isi **Nama/NIM** `Budi - 1301220001` → klik **A · Festival Musik** → **Kirim Suara**.
   👉 Toast hijau, angka Opsi A jadi 1, bar merah 100%. Di Network terlihat request **`POST votes` status 201**.
4. Vote `Sari - 1301220002` → **B**, lalu `Andi - 1301220003` → **A**.
   👉 Bar 66.7% vs 33.3%, badge **🏆 Unggul** di Opsi A.
5. Vote lagi dengan nama **`budi - 1301220001`** (huruf kecil) → **B**.
   👉 Toast merah: *"sudah memberikan suara"* → di Network **status 409**.
6. Di tabel **Catatan Suara**, klik **Hapus** pada baris Sari → tombol berubah jadi **Yakin?** → klik lagi.
   👉 Baris hilang, angka B berkurang, Network: **`DELETE votes?index=1` status 200**.
7. *(Opsional, bagus untuk poin "real-time")*: buka `localhost:8080` di jendela kedua/HP satu WiFi (pakai IP laptop), vote dari sana → jendela pertama ikut berubah dalam ≤5 detik tanpa refresh.

**Ucapkan:**
> "Frontend murni HTML dan Vanilla JavaScript. Semua komunikasi pakai **fetch() asynchronous** ke `/api/votes` — terlihat di tab Network. Halaman auto-refresh setiap 5 detik, jadi hasil polling selalu real-time. Satu pemilih hanya boleh satu suara — backend menolak dengan kode **409 Conflict**."

---

#### 🎬 Adegan 4 — Demo API & error handling (Aizza, ±50 detik)
**Layar:** Terminal.

**Langkah:**
1. Jalankan:
   ```bash
   ./scripts/test-api.sh
   ```
   Tekan **Enter** di setiap langkah sambil menjelaskan kode statusnya:
   `200` health → `200` GET → `201` POST → `409` duplikat → `400` opsi C → `400` JSON rusak → `404` index 999 → `400` index "abc" → `200` DELETE.
2. Tunjukkan file JSON asli di dalam volume:
   ```bash
   docker exec polling-backend cat /var/lib/polling_data/votes.json
   ```

**Ucapkan:**
> "Backend dibuat dengan **standard library Python tanpa framework**. Setiap input salah dijawab dengan kode yang tepat: **400** untuk input tidak valid, **404** untuk data yang tidak ada, **409** untuk vote ganda. Datanya disimpan di `votes.json` yang berada di dalam named volume."

---

#### 🎬 Adegan 5 — Bind Mount (Alfreda, ±30 detik)
**Layar:** VS Code ↔ Browser tab 2.

**Langkah:**
1. Di VS Code buka `frontend/index.html`, cari (Cmd/Ctrl+F) `<h1>Campus Polling System</h1>`.
2. Ubah jadi `<h1>Campus Polling System - DEMO BIND MOUNT</h1>` → **Save**.
3. Pindah ke browser → **refresh** (F5). 👉 Judul langsung berubah.
4. Kembali ke VS Code → **Cmd/Ctrl+Z** → Save → refresh browser (judul kembali).
   ⚠️ **Jangan di-commit** perubahan ini.

**Ucapkan:**
> "Folder `frontend` di laptop di-**bind mount** ke kontainer Nginx. Jadi perubahan UI langsung terlihat **tanpa rebuild image** dan tanpa restart kontainer."

---

#### 🎬 Adegan 6 — Data Immunity (Aizza, ±1 menit)
**Layar:** Terminal + Browser tab 2 (berdampingan kalau bisa).

**Langkah:**
1. Tunjuk di browser: total suara saat ini (misal **Total 3 suara**).
2. Catat ID kontainer lama:
   ```bash
   docker ps --filter name=polling-backend --format '{{.ID}} {{.Names}} {{.Status}}'
   ```
3. **Hapus paksa** kontainer backend:
   ```bash
   docker rm -f polling-backend
   ```
4. Lihat browser → dalam ≤5 detik indikator jadi **API Offline** (merah). Bisa juga:
   ```bash
   curl http://localhost:8080/api/votes
   ```
   👉 `503 Backend API sedang tidak tersedia`.
5. Buktikan volume masih ada:
   ```bash
   docker volume inspect polling-db-data
   ```
6. Buat ulang kontainer backend:
   ```bash
   docker compose up -d backend
   docker ps --filter name=polling-backend --format '{{.ID}} {{.Names}} {{.Status}}'
   ```
   👉 **ID kontainer berbeda** (kontainer baru).
7. Browser kembali **API Online** dan **data masih lengkap** (Total 3 suara, nama-nama sama).

> Alternatif cepat: `./scripts/data-immunity.sh` (otomatis menjalankan langkah 2–7, tekan Enter tiap langkah).

**Ucapkan:**
> "Kontainer kami hapus paksa dengan `docker rm -f`. Kontainer baru punya ID berbeda, tapi **semua suara masih ada**. Ini karena data tidak disimpan di dalam kontainer, melainkan di **named volume `polling-db-data`** yang siklus hidupnya terpisah dari kontainer. Inilah **Data Immunity**."

---

#### 🎬 Adegan 7 — CI/CD: git push → Jenkins otomatis (Bagus, ±2 menit)
**Layar:** VS Code → Terminal → Jenkins (tab 3) → Browser tab 2.

**Langkah:**
1. *(Singkat, 15 detik)* Buka `Jenkinsfile` di VS Code, scroll sambil sebut 5 stage: **Checkout, Syntax Check, Build Image, Automated Deployment, Health Check** dan baris `triggers { githubPush() }`.
2. Buka `docker-compose.yml`, ubah:
   ```yaml
   POLL_QUESTION: "Tema Dies Natalis Fakultas 2026?"
   ```
   menjadi
   ```yaml
   POLL_QUESTION: "Lokasi Makrab Angkatan 2026?"
   ```
   → **Save**.
3. Di terminal:
   ```bash
   git add docker-compose.yml
   git commit -m "feat: ganti pertanyaan polling"
   git push origin main
   ```
4. **Langsung** pindah ke Jenkins (tab 3). **Jangan klik Build Now.**
   👉 Dalam beberapa detik build baru (#N) muncul sendiri di *Build History*.
5. Klik build tersebut → tunjuk tulisan **"Started by GitHub push by …"** → buka **Pipeline Overview / Stage View**, lihat stage berjalan satu per satu sampai **5 hijau**.
6. Buka **Console Output** → scroll ke bawah, tunjuk:
   - hasil unit test `Ran 15 tests … OK`
   - output Health Check `{"status": "ok", ...}` dan `Health check OK`
   - `DEPLOY SUKSES - build #N`
7. *(Opsional bukti)* Tab 4 GitHub Webhooks → **Recent Deliveries** → delivery terbaru status **200**.
8. Pindah ke browser tab 2 → **refresh**.
   👉 Pertanyaan berubah jadi **"Lokasi Makrab Angkatan 2026?"** dan **suara lama tetap ada** (deploy ulang tidak menghapus volume).

**Ucapkan (sambil menunggu pipeline):**
> "Begitu kami push, GitHub mengirim **webhook** ke Jenkins melalui tunnel ngrok. Jenkins otomatis menjalankan pipeline tanpa kami klik apa pun. Stage **Checkout** mengambil kode, **Syntax Check** mengecek sintaks Python dan menjalankan 15 unit test, **Build Image** membangun image backend dengan tag nomor build, **Automated Deployment** menjalankan `docker compose up -d`, dan **Health Check** memanggil `/api/health` dari dalam kontainer Nginx — sekaligus membuktikan DNS di `app-net` berfungsi. Kalau satu stage gagal, deploy dibatalkan sehingga kode rusak tidak pernah sampai ke pengguna.
> Perubahan sudah live, dan suara yang tadi masuk tetap ada."

---

#### 🎬 Adegan 8 — Penutup (Aizza, ±30 detik)
**Layar:** README / kamera.

**Ucapkan:**
> "Kesimpulannya, kami sudah menerapkan tiga hal utama cloud-native: **isolasi** dengan kontainer dan custom network, **persistensi data** dengan named volume, dan **otomatisasi** deployment dengan Jenkins dan GitHub Webhook. Seluruh kode dan dokumentasi ada di repository GitHub kami. Terima kasih."

---

### 7.4 Setelah demo (kembalikan kondisi)
```bash
# Kembalikan pertanyaan polling (opsional) lalu push lagi -> sekalian bukti CI/CD kedua
git pull
# Kembalikan bind mount ke folder lokal (penting kalau mau latihan Adegan 5 lagi)
docker compose up -d
curl -X DELETE "http://localhost:8080/api/votes?index=all"
```

### 7.5 Rencana cadangan (Plan B) saat demo live

| Masalah saat demo | Tindakan cepat |
|---|---|
| Build tidak muncul setelah push (>20 detik) | Cek terminal ngrok ada request `POST /github-webhook/` atau tidak. Cek GitHub Recent Deliveries. Kalau ngrok mati → jalankan lagi, update URL webhook, klik **Redeliver**. Terakhir: klik **Build Now** sambil menunjukkan build sebelumnya yang "Started by GitHub push". |
| Stage merah | Buka Console Output, baca error terakhir — jelaskan bahwa pipeline **menahan deploy** (itu justru fitur). Perbaiki, push lagi. |
| Edit `index.html` tidak berubah (Adegan 5) | Bind mount sedang menunjuk workspace Jenkins → jalankan `docker compose up -d` dari root proyek, refresh. |
| UI "API Offline" di awal | `docker compose ps`; kalau backend tidak healthy → `docker compose logs backend` lalu `docker compose up -d`. |
| Docker Desktop hang | Restart Docker Desktop; kontainer menyala lagi otomatis (`restart: unless-stopped`), data aman di volume. |
| Internet mati | Webhook tidak bisa jalan → tunjukkan **video cadangan** CI/CD yang sudah direkam sebelumnya. |

### 7.6 Tips merekam video
- **Alat rekam:** Mac → QuickTime (File → New Screen Recording) atau OBS; Windows → OBS / Xbox Game Bar (Win+G).
- Rekam **per adegan** lalu gabungkan (CapCut/DaVinci/iMovie) → lebih mudah diulang kalau salah. Tapi **Adegan 7 rekam utuh tanpa potong** (dari `git push` sampai build hijau) supaya terbukti otomatis.
- Resolusi minimal 1080p, font terminal ≥ 16 pt, kursor terlihat jelas.
- Total durasi **5–8 menit** (target ±7:30). Kalau kelebihan, persingkat Adegan 2 dan 4.
- Upload ke YouTube (*Unlisted*) / Google Drive (akses "Anyone with the link") → tempel link di README.

---

## 8. Bank Soal: Pertanyaan Dosen + Jawaban

**Docker & Storage**

1. **Apa beda image dan container?**
   Image adalah template read-only hasil build Dockerfile. Container adalah instance image yang sedang berjalan, dengan lapisan tulis sendiri yang hilang ketika container dihapus.

2. **Kenapa data tidak hilang setelah `docker rm -f`?**
   `votes.json` ditulis ke `/var/lib/polling_data`, dan folder itu di-mount dari Named Volume `polling-db-data`. Volume hidup terpisah dari container, jadi container baru langsung memakai volume yang sama.

3. **Kapan data benar-benar hilang?**
   Saat volume ikut dihapus: `docker compose down -v`, `docker volume rm polling-db-data`, atau `docker volume prune`.

4. **Kenapa database tidak pakai bind mount?**
   Bind mount bergantung pada path dan permission di host, tidak portabel antar-OS, dan file bisa terhapus atau teredit tanpa sengaja. Named volume dikelola Docker dan memang dirancang untuk data aplikasi.

5. **Kenapa frontend pakai bind mount?**
   Supaya perubahan UI langsung terlihat tanpa rebuild image, sesuai ketentuan soal. Mount-nya dibuat `:ro` supaya kontainer tidak bisa mengubah file di host.

6. **Di mana lokasi fisik named volume?**
   Di `/var/lib/docker/volumes/polling-db-data/_data`, bisa dicek dengan `docker volume inspect polling-db-data`. Di Mac/Windows, folder itu berada di dalam VM Docker Desktop.

7. **Kenapa backend pakai user non-root?**
   Prinsip *least privilege*: kalau aplikasi dibobol, penyerang tidak langsung mendapat akses root di dalam kontainer.

**Networking**

8. **Bagaimana frontend tahu alamat backend?**
   Lewat DNS internal Docker (`127.0.0.11`) di custom network `app-net`. Nama service `backend` di-resolve ke IP kontainer backend.

9. **Kenapa harus custom network, tidak pakai default bridge?**
   Network `bridge` default tidak menyediakan resolusi nama antar-container. Custom bridge menyediakan DNS dan mengisolasi stack ini dari container lain.

10. **Kenapa port 5000 tidak dibuka ke host?**
    Supaya backend terisolasi dan satu-satunya pintu masuk adalah Nginx. Permukaan serangan jadi lebih kecil. (Bonus: di macOS, port 5000 juga sudah dipakai AirPlay Receiver.)

11. **Apa arti `8080:80`?**
    Port 8080 di host diteruskan ke port 80 di dalam container Nginx (format `HOST:CONTAINER`).

12. **Apa fungsi `resolver 127.0.0.11` di Nginx?**
    Membuat Nginx me-resolve ulang nama `backend` setiap 10 detik. Setelah backend dibuat ulang dengan IP baru, Nginx tetap bisa menjangkaunya tanpa restart.

**Backend & Frontend**

13. **Error handling apa saja yang ada?**
    400 untuk JSON tidak valid, opsi bukan A/B, voter kosong, atau index bukan angka. 404 untuk index tidak ada atau endpoint salah. 405 untuk method salah. 409 untuk voter yang vote dua kali. 413 untuk body terlalu besar. Error lain menjadi 500 tanpa membuat server crash.

14. **Kalau 2 orang vote bersamaan, apakah datanya bisa rusak?**
    Tidak. Ada `threading.Lock` untuk proses baca-ubah-tulis, dan penulisan file bersifat atomik (file sementara lalu `os.replace`).

15. **Bagaimana UI terasa real-time tanpa refresh?**
    `fetch()` asynchronous, ditambah auto-refresh `setInterval` setiap 5 detik. Setiap aksi POST/DELETE juga langsung memuat ulang data.

16. **Aman dari XSS?**
    Ya. Data dari user dirender dengan `textContent`, bukan `innerHTML`.

**Jenkins & CI/CD**

17. **Jelaskan 5 stage pipeline.**
    Lihat bagian 4.5. Poin utamanya: gagal di stage mana pun berarti tidak ada deploy.

18. **Beda webhook dan polling SCM?**
    Dengan webhook, GitHub yang memberi tahu Jenkins (push-based, instan). Dengan polling, Jenkins yang bertanya ke GitHub tiap beberapa menit (pull-based, ada jeda, boros request).

19. **Kenapa butuh ngrok?**
    Jenkins berjalan di localhost yang tidak bisa diakses dari internet. ngrok membuat URL HTTPS publik yang diteruskan ke port 9090.

20. **Kenapa pakai PAT, bukan password?**
    GitHub tidak lagi menerima password untuk akses Git via HTTPS. PAT bisa dibatasi izinnya (`repo`, `admin:repo_hook`), punya masa berlaku, dan bisa dicabut kapan saja.

21. **Bagaimana Jenkins di dalam container bisa menjalankan `docker`?**
    Socket Docker host di-mount (`/var/run/docker.sock`), jadi Docker CLI di Jenkins memerintah Docker daemon milik laptop. Container yang dibuat adalah "saudara" Jenkins, bukan container di dalam container.

22. **Bagaimana cara rollback?**
    Setiap build diberi tag `campus-polling-backend:<BUILD_NUMBER>`. Untuk rollback: `docker tag campus-polling-backend:<nomor_lama> campus-polling-backend:latest && docker compose up -d`, atau `git revert` lalu push.

23. **Kenapa data tetap ada setelah Jenkins deploy ulang?**
    `docker compose up -d` hanya membuat ulang container. Volume tidak pernah dihapus (Jenkinsfile tidak memakai `down -v`).

---

## 9. Troubleshooting

| Gejala | Penyebab | Solusi |
|---|---|---|
| `Cannot connect to the Docker daemon` | Docker Desktop belum jalan | Buka Docker Desktop, tunggu ikon hijau |
| `port is already allocated` 8080 | Port dipakai aplikasi lain | Ubah `"8080:80"` jadi `"8081:80"` |
| UI tampil, status **API Offline** | Backend mati / belum healthy | `docker compose ps`, `docker compose logs backend` |
| `curl localhost:5000` gagal | Memang disengaja (backend terisolasi). Di Mac, 5000 juga dipakai AirPlay | Pakai `http://localhost:8080/api/...` |
| Nginx 403 / halaman kosong saat deploy dari Jenkins | Path workspace Jenkins beda dengan path host (bind mount kosong) | Jalankan Jenkins dengan `jenkins/docker-compose.yml` (path `${HOME}/jenkins_home` identik) |
| Health check `Connection refused` ke `localhost` di dalam container | `localhost` mengarah ke IPv6 `::1` | Sudah ditangani: Nginx `listen [::]:80` & health check pakai `127.0.0.1` |
| Edit `index.html` di laptop tidak muncul di browser | Stack terakhir di-deploy oleh Jenkins → bind mount menunjuk folder workspace Jenkins | Jalankan `docker compose up -d` dari root folder proyek lokal, lalu refresh |
| Perubahan `default.conf` tidak terpakai | Nginx belum reload | `docker exec polling-frontend nginx -s reload` (sudah otomatis di Jenkinsfile) |
| Jenkins: `docker: not found` / `permission denied ... docker.sock` | Jenkins bukan dari image custom / tidak root | Gunakan `jenkins/docker-compose.yml` (sudah `user: root` + Docker CLI) |
| Jenkins: `python3: not found` | Jenkins image standar | Gunakan image custom `jenkins/Dockerfile` |
| Push tidak memicu build | Webhook salah / ngrok mati / trigger belum aktif | Cek Recent Deliveries di GitHub (harus 200), URL diakhiri `/github-webhook/`, centang *GitHub hook trigger for GITScm polling*, jalankan **Build Now** sekali |
| URL ngrok berubah | ngrok gratis membuat URL baru setiap restart | Update Payload URL webhook di GitHub |
| Checkout gagal `Authentication failed` | PAT salah/kedaluwarsa | Buat PAT baru, update credential `github-pat` |
| Ingin mulai dari nol | – | `docker compose down -v` (⚠️ menghapus semua suara) lalu `docker compose up -d --build` |

---

## 10. Cheat Sheet Perintah & Checklist H-1

```bash
# ---- Menjalankan ----
docker compose up -d --build        # build + jalankan
docker compose ps                   # status (cari "healthy")
docker compose logs -f backend      # log API live
docker compose down                 # stop (data aman)

# ---- Inspeksi (bagus untuk ditunjukkan saat demo) ----
docker network inspect app-net --format '{{range .Containers}}{{.Name}} {{.IPv4Address}}{{"\n"}}{{end}}'
docker volume inspect polling-db-data
docker exec polling-backend cat /var/lib/polling_data/votes.json
docker exec polling-frontend nslookup backend      # bukti DNS service name
docker image ls campus-polling-backend             # tag per BUILD_NUMBER

# ---- API ----
curl http://localhost:8080/api/votes
curl -X POST http://localhost:8080/api/votes -H "Content-Type: application/json" -d '{"voter":"Budi","option":"A"}'
curl -X DELETE "http://localhost:8080/api/votes?index=0"
curl -X DELETE "http://localhost:8080/api/votes?index=all"

# ---- Demo ----
./scripts/test-api.sh
./scripts/data-immunity.sh
python3 -m unittest discover -s tests -v
```

**✅ Checklist H-1 sebelum demo/rekam**
- [x] Nama & NIM semua anggota sudah diisi di README
- [ ] Repo GitHub berisi: `app.py`, `index.html`, `Dockerfile`, `docker-compose.yml`, `Jenkinsfile`, `README.md`
- [ ] `docker compose up -d --build` sukses, backend `(healthy)`
- [ ] Jenkins job sudah pernah hijau via **Build Now**
- [ ] ngrok jalan dan webhook GitHub menunjukkan delivery **200**
- [ ] Sudah tes 1× `git push` → build otomatis muncul ("Started by GitHub push")
- [ ] Data di-reset sebelum rekam
- [ ] Setiap anggota sudah latihan bagiannya di naskah (Bagian 7) & membaca Bank Soal (Bagian 8)
- [ ] Link video sudah ditempel di README
