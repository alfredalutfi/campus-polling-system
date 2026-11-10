#!/usr/bin/env bash
# =============================================================
# Demo REST API Campus Polling System memakai curl
# Pakai saat demo: ./scripts/test-api.sh
# =============================================================
API="${API:-http://localhost:8080/api}"

step() { echo; echo "=================================================="; echo "▶ $1"; echo "=================================================="; }
call() { echo "\$ curl $*"; curl -s -w "\n   ↳ HTTP %{http_code}\n" "$@"; }
pause() { [ -t 0 ] && read -r -p "   (Enter untuk lanjut) " _ || true; }

step "1. Health check (GET /health)"
call "$API/health"; pause

step "2. Lihat perolehan suara (GET /votes)"
call "$API/votes"; pause

step "3. Kirim suara Opsi A (POST /votes) -> 201 Created"
call -X POST "$API/votes" -H "Content-Type: application/json" -d '{"voter":"Demo Curl - 1301229999","option":"A"}'; pause

step "4. Error: pemilih yang sama vote lagi -> 409 Conflict"
call -X POST "$API/votes" -H "Content-Type: application/json" -d '{"voter":"Demo Curl - 1301229999","option":"B"}'; pause

step "5. Error: opsi tidak valid -> 400 Bad Request"
call -X POST "$API/votes" -H "Content-Type: application/json" -d '{"voter":"Orang Lain","option":"C"}'; pause

step "6. Error: body bukan JSON -> 400 Bad Request"
call -X POST "$API/votes" -H "Content-Type: application/json" -d '{ini bukan json'; pause

step "7. Error: hapus index yang tidak ada -> 404 Not Found"
call -X DELETE "$API/votes?index=999"; pause

step "8. Error: index bukan angka -> 400 Bad Request"
call -X DELETE "$API/votes?index=abc"; pause

step "9. Hapus catatan suara terakhir (DELETE /votes?index=X) -> 200 OK"
LAST=$(curl -s "$API/votes" | python3 -c 'import sys,json; print(len(json.load(sys.stdin)["votes"])-1)')
call -X DELETE "$API/votes?index=$LAST"

echo; echo "Selesai. (Reset semua suara: curl -X DELETE \"$API/votes?index=all\")"
