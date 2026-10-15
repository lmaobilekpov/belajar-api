# Master Data API Playground

Aplikasi latihan ini menggunakan **FastAPI**, **SQLite**, dan **SQLAlchemy** sebagai aplikasi pusat data dummy karyawan dan supplier. Aplikasi menyediakan API berautentikasi untuk aplikasi konsumen serta halaman web sederhana untuk mengelola data latihan. Jangan masukkan data karyawan atau supplier nyata ke repo latihan ini.

## Cara Menjalankan Aplikasi

1. Buka terminal/command prompt.
2. Pastikan Anda berada di dalam folder project ini (`c:\Users\Rajendra\Documents\belajar-api`).
3. (Opsional namun disarankan) Buat dan aktifkan virtual environment:
   ```bash
   python -m venv venv
   # Di Windows:
   venv\Scripts\activate
   ```
4. Install semua dependensi yang dibutuhkan:
   ```bash
   pip install -r requirements.txt
   ```
5. Jalankan server FastAPI menggunakan uvicorn:
   ```bash
   uvicorn main:app --reload
   ```

Aplikasi akan otomatis membuat file database `suppliers.db` dan mengisi data awal (seed data) saat pertama kali dijalankan.

## URL Server dan Dokumentasi

Secara default, server akan berjalan di:
- **Base URL API**: `http://127.0.0.1:8000`
- **Dokumentasi API Bawaan (Swagger UI)**: `http://127.0.0.1:8000/docs` *(Buka URL ini di browser untuk mencoba endpoint API secara langsung!)*
- **Dokumentasi ReDoc**: `http://127.0.0.1:8000/redoc`

## Daftar Endpoint

| HTTP Method | Endpoint                    | Deskripsi                                   |
| ----------- | --------------------------- | ------------------------------------------- |
| `GET`       | `/api/suppliers/`           | Mengambil semua data supplier               |
| `GET`       | `/api/suppliers/{id}`       | Mengambil data supplier berdasarkan ID      |
| `POST`      | `/api/suppliers/`           | Menambahkan data supplier baru              |
| `PUT`       | `/api/suppliers/{id}`       | Memperbarui data supplier berdasarkan ID    |
| `DELETE`    | `/api/suppliers/{id}`       | Menghapus data supplier berdasarkan ID      |

## Contoh Request & Response

### 1. GET Semua Supplier
**Request (cURL):**
```bash
curl -X 'GET' 'http://127.0.0.1:8000/api/suppliers/' -H 'accept: application/json'
```
**Response JSON:**
```json
[
  {
    "kode_supplier": "SUP001",
    "nama_supplier": "PT Maju Jaya",
    "alamat": "Jakarta",
    "id": 1
  },
  {
    "kode_supplier": "SUP002",
    "nama_supplier": "PT Sumber Makmur",
    "alamat": "Depok",
    "id": 2
  },
  {
    "kode_supplier": "SUP003",
    "nama_supplier": "CV Berkah Abadi",
    "alamat": "Bogor",
    "id": 3
  }
]
```

### 2. POST (Menambah Supplier Baru)
**Request (cURL):**
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/api/suppliers/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "kode_supplier": "SUP004",
  "nama_supplier": "PT Global Niaga",
  "alamat": "Bandung"
}'
```
**Response JSON:**
```json
{
  "kode_supplier": "SUP004",
  "nama_supplier": "PT Global Niaga",
  "alamat": "Bandung",
  "id": 4
}
```


## Web Master Data Dummy

Install dependensi seperti biasa:
```powershell
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

UI master data lokal:
- Dashboard: `http://127.0.0.1:8000/web/`
- Data karyawan: `http://127.0.0.1:8000/web/employees/`
- Data supplier: `http://127.0.0.1:8000/web/suppliers/`
- Dokumentasi API: `http://127.0.0.1:8000/docs`

Browser akan meminta Basic Auth untuk UI web. Kredensial demo adalah username `jen` dan password `belajar123`. UI ini hanya untuk latihan lokal dan bukan panel produksi.

API untuk sinkronisasi konsumen:
- `POST /token`: mendapat access token melalui username dan password demo.
- `GET /api/employees/`: daftar karyawan dummy lengkap, termasuk yang nonaktif.
- `GET /api/employees/{id}`: detail karyawan dummy.
- `POST /api/employees/`, `PUT /api/employees/{id}`, `DELETE /api/employees/{id}`: kelola record karyawan via API.
- `GET /api/suppliers/` dan `GET /api/suppliers/{id}`: daftar/detail supplier.
- CRUD supplier yang ada tetap tersedia.
- `/test-timeout`: endpoint latihan yang sengaja menunggu enam detik.

Endpoint daftar karyawan dan supplier pada playground ini mengembalikan daftar lengkap dan belum menggunakan pagination. Ini disederhanakan untuk latihan sinkronisasi lokal; jangan mengasumsikan API kantor memiliki perilaku yang sama.
