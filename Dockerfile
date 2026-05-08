# Menggunakan image Python yang ringan
FROM python:3.9-slim

# Mengatur direktori kerja di dalam container
WORKDIR /app

# Menyalin file konfigurasi library terlebih dahulu
COPY requirements.txt .

# Menginstal semua library yang dibutuhkan
RUN pip install --no-cache-dir -r requirements.txt

# Menyalin seluruh source code ke dalam container
COPY . .

# Mengekspos port 5000 agar bisa diakses
EXPOSE 5000

# Perintah untuk menjalankan aplikasi Flask
CMD ["python", "app.py"]