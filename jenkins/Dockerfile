# =============================================================
# Image Jenkins custom untuk praktikum
#   jenkins/jenkins:lts + Docker CLI + Buildx + Compose plugin + Python3
# Jenkins memakai Docker milik host lewat /var/run/docker.sock
# =============================================================
FROM jenkins/jenkins:lts-jdk17

USER root

# Docker CLI + Compose plugin dari repository resmi Docker, plus python3 & git
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl gnupg python3 git \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc \
    && chmod a+r /etc/apt/keyrings/docker.asc \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
       > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends docker-ce-cli docker-buildx-plugin docker-compose-plugin \
    && rm -rf /var/lib/apt/lists/*

# Plugin Jenkins yang dibutuhkan pipeline ini
RUN jenkins-plugin-cli --plugins \
    workflow-aggregator \
    git \
    github \
    credentials-binding \
    pipeline-stage-view

# Catatan: dijalankan sebagai root agar bisa mengakses docker.sock.
# Ini CUKUP untuk lingkungan praktikum/lab, BUKAN untuk produksi.
