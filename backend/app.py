#!/usr/bin/env python3
"""
Campus Polling System - Backend REST API
=========================================
Studi Kasus 7 - Ujian Chunin Cloud Computing (Telkom University)

Dibangun HANYA dengan Python standard library (tanpa Flask/Django) sesuai
ketentuan tugas: "Python REST API tanpa framework berat".

Endpoint:
    GET    /health              -> status layanan (dipakai Jenkins Health Check)
    GET    /votes               -> perolehan suara Opsi A vs B + riwayat suara
    POST   /votes               -> kirim suara  body: {"voter": "...", "option": "A"|"B"}
    DELETE /votes?index=X       -> hapus 1 catatan suara pada index X
    DELETE /votes?index=all     -> reset seluruh catatan suara

Penyimpanan:
    File JSON  ->  $DATA_DIR/votes.json  (default: /var/lib/polling_data/votes.json)
    Folder $DATA_DIR di-mount ke Docker Named Volume "polling-db-data",
    sehingga data TETAP ADA walaupun kontainer dihapus (docker rm -f).
"""

import json
import os
import sys
import tempfile
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

# ---------------------------------------------------------------------------
# Konfigurasi (bisa diubah lewat environment variable di docker-compose.yml)
# ---------------------------------------------------------------------------
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))
DATA_DIR = os.environ.get("DATA_DIR", "/var/lib/polling_data")
DATA_FILE = os.path.join(DATA_DIR, "votes.json")

POLL_QUESTION = os.environ.get("POLL_QUESTION", "Tema Dies Natalis Fakultas 2026?")
OPTIONS = {
    "A": os.environ.get("OPTION_A", "Festival Musik"),
    "B": os.environ.get("OPTION_B", "Pameran Teknologi"),
}

MAX_BODY_BYTES = 10 * 1024  # tolak body > 10 KB (413)
MAX_VOTER_LEN = 60

# Lock supaya dua request yang datang bersamaan tidak saling menimpa file JSON
_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Lapisan penyimpanan (storage) - baca/tulis votes.json
# ---------------------------------------------------------------------------
def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_votes():
    """Baca seluruh catatan suara dari votes.json. File belum ada -> list kosong."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        raise ValueError("isi votes.json bukan list")
    except (ValueError, OSError) as exc:
        # File rusak: amankan sebagai backup supaya tidak tertimpa diam-diam
        backup = f"{DATA_FILE}.corrupt-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        try:
            os.replace(DATA_FILE, backup)
        except OSError:
            pass
        print(f"[WARN] votes.json tidak valid ({exc}); dipindah ke {backup}", flush=True)
        return []


def save_votes(votes):
    """Tulis votes.json secara ATOMIK: tulis ke file sementara lalu rename.
    Jika kontainer mati di tengah penulisan, file lama tidak rusak."""
    os.makedirs(DATA_DIR, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=DATA_DIR, prefix=".votes-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(votes, f, ensure_ascii=False, indent=2)
        os.chmod(tmp_path, 0o644)  # mkstemp membuat file 0600; buat agar bisa dibaca saat demo
        os.replace(tmp_path, DATA_FILE)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def summarize(votes):
    """Hitung perolehan suara Opsi A vs B."""
    count = {key: 0 for key in OPTIONS}
    for v in votes:
        if v.get("option") in count:
            count[v["option"]] += 1
    total = sum(count.values())
    percent = {k: (round(c * 100 / total, 1) if total else 0.0) for k, c in count.items()}

    if total == 0:
        leader = None
    elif count["A"] == count["B"]:
        leader = "SERI"
    else:
        leader = "A" if count["A"] > count["B"] else "B"

    return {"count": count, "percent": percent, "total": total, "leader": leader}


def build_state(votes):
    """Bentuk respons lengkap GET /votes."""
    return {
        "poll": {"question": POLL_QUESTION, "options": OPTIONS},
        "results": summarize(votes),
        "votes": [
            {
                "index": i,
                "voter": v.get("voter"),
                "option": v.get("option"),
                "label": OPTIONS.get(v.get("option"), "?"),
                "timestamp": v.get("timestamp"),
            }
            for i, v in enumerate(votes)
        ],
    }


# ---------------------------------------------------------------------------
# HTTP Handler
# ---------------------------------------------------------------------------
class ApiError(Exception):
    """Error yang sudah 'dikenali' -> dikirim ke klien sebagai JSON {error: ...}."""

    def __init__(self, status, message, headers=None):
        super().__init__(message)
        self.status = status
        self.message = message
        self.headers = headers or {}


class PollingHandler(BaseHTTPRequestHandler):
    server_version = "CampusPollingAPI/1.0"

    # ---- helper respons -------------------------------------------------
    def _send_json(self, status, payload, extra_headers=None):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _route(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        return path, parse_qs(parsed.query)

    def _read_json_body(self):
        length_header = self.headers.get("Content-Length")
        if not length_header:
            raise ApiError(400, "Body request kosong. Kirim JSON: {\"voter\": \"...\", \"option\": \"A\"}")
        try:
            length = int(length_header)
        except ValueError:
            raise ApiError(400, "Header Content-Length tidak valid")
        if length > MAX_BODY_BYTES:
            raise ApiError(413, f"Body terlalu besar (maks {MAX_BODY_BYTES} byte)")
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ApiError(400, "Body bukan JSON yang valid")
        if not isinstance(data, dict):
            raise ApiError(400, "Body JSON harus berupa object {...}")
        return data

    def _dispatch(self, method):
        """Panggil handler sesuai method + path; tangani semua error di satu tempat."""
        try:
            path, query = self._route()
            routes = {
                ("GET", "/"): self.handle_root,
                ("GET", "/health"): self.handle_health,
                ("GET", "/votes"): self.handle_get_votes,
                ("POST", "/votes"): self.handle_post_votes,
                ("DELETE", "/votes"): self.handle_delete_votes,
            }
            handler = routes.get((method, path))
            if handler:
                return handler(query)

            allowed = sorted(m for (m, p) in routes if p == path)
            if allowed:  # path ada, tapi method salah
                raise ApiError(405, f"Method {method} tidak diizinkan untuk {path}. Gunakan: {', '.join(allowed)}",
                               {"Allow": ", ".join(allowed)})
            raise ApiError(404, f"Endpoint {path} tidak ditemukan")
        except ApiError as err:
            self._send_json(err.status, {"error": err.message, "status": err.status}, err.headers)
        except Exception as exc:  # error tak terduga -> 500, server tetap hidup
            print(f"[ERROR] {exc!r}", file=sys.stderr, flush=True)
            self._send_json(500, {"error": "Terjadi kesalahan internal pada server", "status": 500})

    # ---- method HTTP ----------------------------------------------------
    def do_GET(self):
        self._dispatch("GET")

    def do_HEAD(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")

    def do_DELETE(self):
        self._dispatch("DELETE")

    def do_PUT(self):
        self._dispatch("PUT")

    def do_PATCH(self):
        self._dispatch("PATCH")

    def do_OPTIONS(self):
        # Preflight CORS (kalau frontend memanggil API dari origin lain)
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", "0")
        self.end_headers()

    # ---- endpoint -------------------------------------------------------
    def handle_root(self, _query):
        self._send_json(200, {
            "service": "Campus Polling System API",
            "endpoints": {
                "GET /health": "status layanan",
                "GET /votes": "perolehan suara + riwayat",
                "POST /votes": "kirim suara {voter, option: A|B}",
                "DELETE /votes?index=X": "hapus catatan suara ke-X",
                "DELETE /votes?index=all": "reset semua suara",
            },
        })

    def handle_health(self, _query):
        with _lock:
            total = len(load_votes())
        self._send_json(200, {
            "status": "ok",
            "service": "polling-backend",
            "data_file": DATA_FILE,
            "total_votes": total,
            "time": _now_iso(),
        })

    def handle_get_votes(self, _query):
        with _lock:
            votes = load_votes()
        self._send_json(200, build_state(votes))

    def handle_post_votes(self, _query):
        data = self._read_json_body()

        option = str(data.get("option", "")).strip().upper()
        if option not in OPTIONS:
            raise ApiError(400, "Field 'option' wajib diisi dengan 'A' atau 'B'")

        voter = str(data.get("voter", "")).strip()
        if not voter:
            raise ApiError(400, "Field 'voter' (nama / NIM pemilih) wajib diisi")
        if len(voter) > MAX_VOTER_LEN:
            raise ApiError(400, f"Field 'voter' maksimal {MAX_VOTER_LEN} karakter")

        with _lock:
            votes = load_votes()
            # Aturan polling: 1 pemilih = 1 suara
            if any(str(v.get("voter", "")).lower() == voter.lower() for v in votes):
                raise ApiError(409, f"'{voter}' sudah memberikan suara. Satu pemilih hanya boleh satu suara.")
            new_vote = {"voter": voter, "option": option, "timestamp": _now_iso()}
            votes.append(new_vote)
            save_votes(votes)
            state = build_state(votes)

        self._send_json(201, {
            "message": f"Suara untuk Opsi {option} ({OPTIONS[option]}) berhasil dicatat",
            "vote": {"index": len(votes) - 1, **new_vote},
            "results": state["results"],
        })

    def handle_delete_votes(self, query):
        raw_index = query.get("index", [None])[0]
        if raw_index is None or raw_index.strip() == "":
            raise ApiError(400, "Parameter 'index' wajib diisi, contoh: DELETE /votes?index=0 atau ?index=all")
        raw_index = raw_index.strip()

        with _lock:
            votes = load_votes()

            # Reset seluruh catatan suara
            if raw_index.lower() == "all":
                deleted_count = len(votes)
                save_votes([])
                self._send_json(200, {
                    "message": f"Reset berhasil: {deleted_count} catatan suara dihapus",
                    "deleted_count": deleted_count,
                    "results": summarize([]),
                })
                return

            try:
                index = int(raw_index)
            except ValueError:
                raise ApiError(400, f"Parameter 'index' harus berupa angka atau 'all', bukan '{raw_index}'")
            if index < 0 or index >= len(votes):
                raise ApiError(404, f"Catatan suara dengan index {index} tidak ditemukan (total: {len(votes)})")

            deleted = votes.pop(index)
            save_votes(votes)
            results = summarize(votes)

        self._send_json(200, {
            "message": f"Catatan suara index {index} ({deleted.get('voter')}) berhasil dihapus",
            "deleted": deleted,
            "results": results,
        })

    # Log ke stdout supaya terlihat di `docker logs polling-backend`
    def log_message(self, fmt, *args):
        print(f"[{_now_iso()}] {self.address_string()} - {fmt % args}", flush=True)


def create_server(host=HOST, port=PORT):
    return ThreadingHTTPServer((host, port), PollingHandler)


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    server = create_server()
    print(f"Campus Polling API berjalan di http://{HOST}:{PORT}", flush=True)
    print(f"Data disimpan di: {DATA_FILE}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
