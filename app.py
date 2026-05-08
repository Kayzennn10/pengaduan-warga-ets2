from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv
import boto3
import pymysql
import os
import uuid

# Load kunci rahasia dari file .env
load_dotenv()

app = Flask(__name__)

# Konfigurasi Koneksi Boto3 ke S3
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
    region_name=os.environ.get('AWS_REGION')
)
BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')

# Fungsi Koneksi ke RDS MySQL
def get_db_connection():
    # Pertama connect ke RDS tanpa nama database (karena belum dibuat)
    conn = pymysql.connect(
        host=os.environ.get('RDS_HOST'),
        user=os.environ.get('RDS_USER'),
        password=os.environ.get('RDS_PASSWORD'),
        cursorclass=pymysql.cursors.DictCursor
    )
    # Buat database dan tabel secara otomatis jika belum ada!
    with conn.cursor() as cursor:
        cursor.execute("CREATE DATABASE IF NOT EXISTS db_pengaduan_desa;")
        cursor.execute("USE db_pengaduan_desa;")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS laporan (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nama VARCHAR(255) NOT NULL,
                keluhan TEXT NOT NULL,
                foto_url VARCHAR(255) NOT NULL,
                status VARCHAR(50) DEFAULT 'Menunggu'
            )
        """)
    conn.commit()
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pengaduan', methods=['GET', 'POST'])
def form_pengaduan():
    if request.method == 'POST':
        nama = request.form.get('nama')
        keluhan = request.form.get('keluhan')
        foto = request.files.get('foto')
        
        foto_url = "Tidak ada foto"
        
        # 1. LOGIKA UPLOAD KE S3
        if foto and foto.filename != '':
            # Bikin nama file unik pakai UUID biar ga bentrok
            nama_file_unik = f"{uuid.uuid4().hex}_{foto.filename}"
            try:
                s3_client.upload_fileobj(
                    foto,
                    BUCKET_NAME,
                    nama_file_unik,
                    ExtraArgs={'ContentType': foto.content_type}
                )
                # Sementara kita pakai URL langsung S3. 
                # (Nanti kalau CloudFront udah di-ACC, kita tinggal ganti sebaris ini!)
                foto_url = f"https://{BUCKET_NAME}.s3.{os.environ.get('AWS_REGION')}.amazonaws.com/{nama_file_unik}"
            except Exception as e:
                print("Gagal upload S3:", e)
                
        # 2. LOGIKA INSERT KE RDS
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO laporan (nama, keluhan, foto_url) VALUES (%s, %s, %s)",
                    (nama, keluhan, foto_url)
                )
            conn.commit()
            conn.close()
        except Exception as e:
            print("Gagal simpan ke RDS:", e)

        return redirect(url_for('dashboard'))
    return render_template('form.html')

@app.route('/dashboard')
def dashboard():
    laporan_masuk = []
    try:
        # Mengambil data asli dari RDS
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("USE db_pengaduan_desa;")
            cursor.execute("SELECT * FROM laporan ORDER BY id DESC")
            laporan_masuk = cursor.fetchall()
        conn.close()
    except Exception as e:
        print("Gagal tarik data RDS:", e)
        
    return render_template('dashboard.html', laporan=laporan_masuk)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)