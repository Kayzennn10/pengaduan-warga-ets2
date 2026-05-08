import os
from flask import Flask, render_template, request, redirect, url_for
import pymysql
import boto3
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Konfigurasi Database (Dihapus bagian 'db' agar tidak nyasar ke sistem AWS)
db_config = {
    'host': os.getenv('RDS_HOST'),
    'user': os.getenv('RDS_USER'),
    'password': os.getenv('RDS_PASSWORD'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# Konfigurasi S3
s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION', 'ap-southeast-2')
)
BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'pengaduan-desa-azka-2026')

def get_connection():
    # Bikin koneksi, buat database db_desa kalau belum ada, lalu gunakan db_desa
    conn = pymysql.connect(**db_config)
    with conn.cursor() as cursor:
        cursor.execute("CREATE DATABASE IF NOT EXISTS db_desa;")
        cursor.execute("USE db_desa;")
    return conn

def init_db():
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            create_table_query = """
            CREATE TABLE IF NOT EXISTS laporan (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nama_pelapor VARCHAR(100),
                keluhan TEXT,
                foto_url VARCHAR(255),
                status VARCHAR(20) DEFAULT 'Pending'
            );
            """
            cursor.execute(create_table_query)
        conn.commit()
        print("✅ Tabel laporan berhasil dipastikan ada!")
    except Exception as e:
        print(f"❌ Gagal buat tabel: {e}")
    finally:
        if conn:
            conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pengaduan', methods=['POST'])
def pengaduan():
    nama = request.form['nama']
    keluhan = request.form['keluhan']
    file = request.files['foto']

    if file:
        file_path = file.filename
        s3.upload_fileobj(file, BUCKET_NAME, file_path)
        foto_url = f"https://{BUCKET_NAME}.s3.ap-southeast-2.amazonaws.com/{file_path}"

        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                sql = "INSERT INTO laporan (nama_pelapor, keluhan, foto_url) VALUES (%s, %s, %s)"
                cursor.execute(sql, (nama, keluhan, foto_url))
            conn.commit()
        except Exception as e:
            print(f"Error DB: {e}")
        finally:
            if conn:
                conn.close()

    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    data_laporan = []
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM laporan ORDER BY id DESC")
            data_laporan = cursor.fetchall()
    except Exception as e:
        print(f"Error DB: {e}")
    finally:
        if conn:
            conn.close()
    return render_template('dashboard.html', laporan=data_laporan)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)