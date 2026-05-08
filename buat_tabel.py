import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

# Koneksi ke RDS
try:
    connection = pymysql.connect(
        host=os.environ.get('RDS_HOST'),
        user=os.environ.get('RDS_USER'),
        password=os.environ.get('RDS_PASSWORD'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    
    with connection.cursor() as cursor:
        # 1. Buat Database
        cursor.execute("CREATE DATABASE IF NOT EXISTS pengaduan_db")
        cursor.execute("USE pengaduan_db")
        
        # 2. Buat Tabel
        sql = """
        CREATE TABLE IF NOT EXISTS laporan (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nama_pelapor VARCHAR(100),
            keluhan TEXT,
            foto_url VARCHAR(255),
            status VARCHAR(20) DEFAULT 'Pending'
        )
        """
        cursor.execute(sql)
        print("✅ Database dan Tabel 'laporan' berhasil dibuat!")
        
    connection.commit()
finally:
    connection.close()