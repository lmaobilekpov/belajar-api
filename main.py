from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm import declarative_base

# 1. Setup Database SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./suppliers.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. Database Model (SQLAlchemy)
class SupplierDB(Base):
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    kode_supplier = Column(String, unique=True, index=True)
    nama_supplier = Column(String)
    alamat = Column(String)

# 3. Pydantic Models untuk Request dan Response
class SupplierBase(BaseModel):
    kode_supplier: str
    nama_supplier: str
    alamat: str

class SupplierCreate(SupplierBase):
    pass

class SupplierResponse(SupplierBase):
    id: int

    class Config:
        from_attributes = True

# 4. Inisialisasi FastAPI
app = FastAPI(
    title="Supplier API Playground",
    description="Aplikasi server API sederhana untuk belajar konsep REST API",
    version="1.0.0"
)

# Authentication sederhana untuk latihan
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != "belajar-api-123":
        raise HTTPException(status_code=401, detail="Token tidak valid")
    return credentials

# Dependency untuk mendapatkan koneksi database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Event startup: buat tabel dan isi seed data jika kosong
@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if db.query(SupplierDB).count() == 0:
        seed_data = [
            SupplierDB(kode_supplier="SUP001", nama_supplier="PT Maju Jaya", alamat="Jakarta"),
            SupplierDB(kode_supplier="SUP002", nama_supplier="PT Sumber Makmur", alamat="Depok"),
            SupplierDB(kode_supplier="SUP003", nama_supplier="CV Berkah Abadi", alamat="Bogor"),
        ]
        db.add_all(seed_data)
        db.commit()
    db.close()

# 5. REST API Endpoints

# GET /api/suppliers/
@app.get("/api/suppliers/", response_model=list[SupplierResponse], dependencies=[Depends(verify_token)])
def get_all_suppliers(search: str | None = None, db: Session = Depends(get_db)):
    query = db.query(SupplierDB)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                SupplierDB.kode_supplier.ilike(search_pattern),
                SupplierDB.nama_supplier.ilike(search_pattern),
                SupplierDB.alamat.ilike(search_pattern)
            )
        )

    return query.all()

# GET /api/suppliers/{id}
@app.get("/api/suppliers/{supplier_id}", response_model=SupplierResponse, dependencies=[Depends(verify_token)])
def get_supplier_by_id(supplier_id: int, db: Session = Depends(get_db)):
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier tidak ditemukan")
    return supplier

# POST /api/suppliers/
@app.post("/api/suppliers/", response_model=SupplierResponse, status_code=201, dependencies=[Depends(verify_token)])
def create_supplier(supplier: SupplierCreate, db: Session = Depends(get_db)):
    # Gunakan model_dump jika Pydantic v2, atau dict untuk v1. Kita gunakan model_dump dengan fallback dict.
    supplier_data = supplier.model_dump() if hasattr(supplier, "model_dump") else supplier.dict()
    db_supplier = SupplierDB(**supplier_data)
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier

# PUT /api/suppliers/{id}
@app.put("/api/suppliers/{supplier_id}", response_model=SupplierResponse, dependencies=[Depends(verify_token)])
def update_supplier(supplier_id: int, supplier_update: SupplierCreate, db: Session = Depends(get_db)):
    db_supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if db_supplier is None:
        raise HTTPException(status_code=404, detail="Supplier tidak ditemukan")
    
    update_data = supplier_update.model_dump() if hasattr(supplier_update, "model_dump") else supplier_update.dict()
    for key, value in update_data.items():
        setattr(db_supplier, key, value)
    
    db.commit()
    db.refresh(db_supplier)
    return db_supplier

# DELETE /api/suppliers/{id}
@app.delete("/api/suppliers/{supplier_id}", dependencies=[Depends(verify_token)])
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)):
    db_supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if db_supplier is None:
        raise HTTPException(status_code=404, detail="Supplier tidak ditemukan")
    
    db.delete(db_supplier)
    db.commit()
    return {"message": f"Supplier dengan id {supplier_id} berhasil dihapus"}
