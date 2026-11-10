// =============================================================
// Jenkinsfile (Declarative Pipeline) - Campus Polling System
// =============================================================
// Alur: git push ke branch main -> GitHub Webhook -> Jenkins menjalankan
// 5 stage: Checkout -> Syntax Check -> Build Image -> Automated Deployment -> Health Check

pipeline {
    agent any

    // Trigger otomatis dari GitHub Webhook (butuh plugin "GitHub")
    triggers {
        githubPush()
    }

    options {
        disableConcurrentBuilds()                       // jangan deploy 2 build bersamaan
        buildDiscarder(logRotator(numToKeepStr: '10'))  // simpan 10 riwayat build terakhir
        timeout(time: 15, unit: 'MINUTES')
    }

    environment {
        COMPOSE_PROJECT_NAME = 'campus-polling'
        BACKEND_IMAGE        = 'campus-polling-backend'
        FRONTEND_CONTAINER   = 'polling-frontend'
    }

    stages {

        // 1) Ambil kode terbaru dari GitHub
        stage('Checkout') {
            steps {
                checkout scm
                sh 'echo "Commit terbaru:" && git log -1 --pretty=format:"%h - %an: %s"'
            }
        }

        // 2) Cek sintaks & jalankan unit test sebelum membangun image
        stage('Syntax Check') {
            steps {
                sh '''
                    echo "== Cek sintaks Python =="
                    python3 -m py_compile backend/app.py

                    echo "== Unit test Backend API =="
                    python3 -m unittest discover -s tests -v

                    echo "== Validasi docker-compose.yml =="
                    docker compose config --quiet

                    echo "== Cek file frontend =="
                    test -s frontend/index.html
                    grep -q "fetch(" frontend/index.html

                    echo "Semua pengecekan lolos."
                '''
            }
        }

        // 3) Build Docker image backend (diberi tag nomor build + latest)
        stage('Build Image') {
            steps {
                sh '''
                    docker build \
                        -t ${BACKEND_IMAGE}:${BUILD_NUMBER} \
                        -t ${BACKEND_IMAGE}:latest \
                        ./backend
                    docker image ls ${BACKEND_IMAGE}
                '''
            }
        }

        // 4) Deploy ulang stack dengan Docker Compose
        //    Named Volume polling-db-data TIDAK dihapus -> data suara tetap aman
        stage('Automated Deployment') {
            steps {
                sh '''
                    docker compose up -d --remove-orphans
                    # Muat ulang config Nginx jika default.conf ikut berubah di commit ini
                    docker exec ${FRONTEND_CONTAINER} nginx -s reload
                    docker compose ps
                '''
            }
        }

        // 5) Pastikan aplikasi benar-benar hidup:
        //    request dikirim dari kontainer frontend (Nginx) -> /api/health -> backend:5000
        //    Sekaligus membuktikan DNS service name di app-net berfungsi.
        stage('Health Check') {
            steps {
                sh '''
                    for i in $(seq 1 15); do
                        if docker exec ${FRONTEND_CONTAINER} wget -qO- http://127.0.0.1/api/health; then
                            echo ""
                            echo "Health check OK (percobaan ke-$i)"
                            exit 0
                        fi
                        echo "Belum siap, coba lagi dalam 3 detik... ($i/15)"
                        sleep 3
                    done
                    echo "Health check GAGAL"
                    docker compose logs --tail=50
                    exit 1
                '''
            }
        }
    }

    post {
        success {
            echo "DEPLOY SUKSES - build #${env.BUILD_NUMBER}. Buka http://localhost:8080"
        }
        failure {
            echo "PIPELINE GAGAL - cek log stage yang berwarna merah."
        }
        always {
            // Bersihkan image lama yang tidak terpakai (dangling)
            sh 'docker image prune -f || true'
        }
    }
}
