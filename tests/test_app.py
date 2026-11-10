"""
Unit test Backend Campus Polling API.
Dijalankan otomatis oleh Jenkins pada stage "Syntax Check".

Jalankan manual:  python3 -m unittest discover -s tests -v
"""
import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

# Pakai folder sementara agar test tidak menyentuh data asli
_TMP_DIR = tempfile.mkdtemp(prefix="polling-test-")
os.environ["DATA_DIR"] = _TMP_DIR
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import app  # noqa: E402


class PollingApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = app.create_server("127.0.0.1", 0)  # port 0 = pilih port kosong
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        if os.path.exists(app.DATA_FILE):
            os.remove(app.DATA_FILE)

    # ---------- helper ----------
    def request(self, method, path, body=None, raw=None):
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        req = urllib.request.Request(self.base + path, data=data, method=method)
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req) as res:
                return res.status, json.loads(res.read())
        except urllib.error.HTTPError as err:
            return err.code, json.loads(err.read())

    def vote(self, voter, option):
        return self.request("POST", "/votes", {"voter": voter, "option": option})

    # ---------- test ----------
    def test_health(self):
        status, body = self.request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "ok")

    def test_get_votes_empty(self):
        status, body = self.request("GET", "/votes")
        self.assertEqual(status, 200)
        self.assertEqual(body["results"]["total"], 0)
        self.assertEqual(body["votes"], [])
        self.assertIn("A", body["poll"]["options"])

    def test_post_vote_and_count(self):
        self.assertEqual(self.vote("Budi", "A")[0], 201)
        self.assertEqual(self.vote("Sari", "a")[0], 201)  # huruf kecil tetap diterima
        self.assertEqual(self.vote("Andi", "B")[0], 201)
        _, body = self.request("GET", "/votes")
        self.assertEqual(body["results"]["count"], {"A": 2, "B": 1})
        self.assertEqual(body["results"]["leader"], "A")
        self.assertEqual(body["results"]["percent"]["A"], 66.7)

    def test_data_saved_to_json_file(self):
        self.vote("Budi", "B")
        with open(app.DATA_FILE, encoding="utf-8") as f:
            saved = json.load(f)
        self.assertEqual(saved[0]["voter"], "Budi")
        self.assertEqual(saved[0]["option"], "B")

    def test_post_invalid_option_400(self):
        status, body = self.vote("Budi", "C")
        self.assertEqual(status, 400)
        self.assertIn("error", body)

    def test_post_missing_voter_400(self):
        status, _ = self.request("POST", "/votes", {"option": "A"})
        self.assertEqual(status, 400)

    def test_post_invalid_json_400(self):
        status, _ = self.request("POST", "/votes", raw=b"{bukan json")
        self.assertEqual(status, 400)

    def test_post_duplicate_voter_409(self):
        self.vote("Budi", "A")
        status, _ = self.vote("budi", "B")  # beda huruf besar/kecil tetap dianggap sama
        self.assertEqual(status, 409)

    def test_delete_by_index(self):
        self.vote("Budi", "A")
        self.vote("Sari", "B")
        status, body = self.request("DELETE", "/votes?index=0")
        self.assertEqual(status, 200)
        self.assertEqual(body["deleted"]["voter"], "Budi")
        _, state = self.request("GET", "/votes")
        self.assertEqual([v["voter"] for v in state["votes"]], ["Sari"])

    def test_delete_missing_index_400(self):
        self.assertEqual(self.request("DELETE", "/votes")[0], 400)

    def test_delete_non_numeric_index_400(self):
        self.assertEqual(self.request("DELETE", "/votes?index=abc")[0], 400)

    def test_delete_out_of_range_404(self):
        self.vote("Budi", "A")
        self.assertEqual(self.request("DELETE", "/votes?index=5")[0], 404)
        self.assertEqual(self.request("DELETE", "/votes?index=-1")[0], 404)

    def test_reset_all(self):
        self.vote("Budi", "A")
        self.vote("Sari", "B")
        status, body = self.request("DELETE", "/votes?index=all")
        self.assertEqual(status, 200)
        self.assertEqual(body["deleted_count"], 2)
        self.assertEqual(self.request("GET", "/votes")[1]["results"]["total"], 0)

    def test_unknown_endpoint_404(self):
        self.assertEqual(self.request("GET", "/tidak-ada")[0], 404)

    def test_wrong_method_405(self):
        self.assertEqual(self.request("PUT", "/votes", {"x": 1})[0], 405)


if __name__ == "__main__":
    unittest.main(verbosity=2)
