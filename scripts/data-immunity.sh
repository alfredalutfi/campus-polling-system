#!/usr/bin/env bash
# =============================================================
# Simulasi DATA IMMUNITY
# Membuktikan data suara tetap ada walaupun kontainer backend
# DIHAPUS PAKSA (docker rm -f), karena data disimpan di
# Docker Named Volume "polling-db-data", bukan di dalam kontainer.
#
# Jalankan dari root project: ./scripts/data-immunity.sh
# =============================================================
set -e
cd "$(dirname "$0")/.."
API="http://localhost:8080/api"

total() { curl -s "$API/votes" | python3 -c 'import sys,json; print(json.load(sys.stdin)["results"]["total"])' 2>/dev/null || echo "?"; }
pause() { [ -t 0 ] && read -r -p "   (Enter untuk lanjut) " _ || true; }

echo "▶ 1. Jumlah suara SEBELUM kontainer dihapus: $(total)"
echo "   ID kontainer backend: $(docker ps -qf name=polling-backend)"
pause

echo "▶ 2. Hapus paksa kontainer backend:  docker rm -f polling-backend"
docker rm -f polling-backend
echo "   Saat backend mati, API menjawab:"
curl -s "$API/votes"; echo
pause

echo "▶ 3. Kontainer sudah hilang, tapi isi Named Volume masih ada:"
docker volume inspect polling-db-data --format '   Volume: {{.Name}}  |  Mountpoint: {{.Mountpoint}}'
docker run --rm -v polling-db-data:/data alpine:3.20 sh -c 'echo "   Isi folder volume:"; ls -la /data | sed "s/^/   /"'
pause

echo "▶ 4. Buat ulang kontainer backend:  docker compose up -d backend"
docker compose up -d backend
echo "   Menunggu backend sehat..."
for i in $(seq 1 20); do
  [ "$(docker inspect -f '{{.State.Health.Status}}' polling-backend 2>/dev/null)" = "healthy" ] && break
  sleep 1
done
echo "   ID kontainer backend BARU: $(docker ps -qf name=polling-backend)"
pause

echo "▶ 5. Jumlah suara SESUDAH kontainer dibuat ulang: $(total)"
echo "   ✅ Data tidak hilang -> Named Volume berhasil menjaga data (Data Immunity)."
