# =============================================================
# Dockerfile - Backend Campus Polling API (Python, tanpa framework)
# =============================================================
# Base image resmi Python versi slim (ukuran kecil, berbasis Debian)
FROM python:3.12-slim

# PYTHONUNBUFFERED=1  -> log langsung muncul di `docker logs`
# PYTHONDONTWRITEBYTECODE=1 -> tidak membuat file .pyc di dalam kontainer
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOST=0.0.0.0 \
    PORT=5000 \
    DATA_DIR=/var/lib/polling_data

WORKDIR /app

# Buat user non-root (best practice keamanan) + folder data yang dimiliki user tsb.
# Saat Named Volume dibuat pertama kali, Docker menyalin kepemilikan folder ini.
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /var/lib/polling_data \
    && chown -R appuser:appuser /var/lib/polling_data

COPY app.py .

USER appuser

# Folder ini yang akan diisi Docker Named Volume "polling-db-data"
VOLUME ["/var/lib/polling_data"]

# Port internal kontainer (TIDAK dipublish ke host; diakses Nginx via network app-net)
EXPOSE 5000

# Docker akan mengecek kesehatan kontainer setiap 10 detik
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=2)" || exit 1

CMD ["python", "app.py"]
