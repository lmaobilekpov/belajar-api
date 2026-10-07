from datetime import datetime, timedelta, timezone

import jwt
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from pwdlib import PasswordHash
from sqlalchemy import create_engine, Column, Integer, String, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm import declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./suppliers.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class SupplierDB(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True, index=True)
    kode_supplier = Column(String, unique=True, index=True)
    nama_supplier = Column(String)
    alamat = Column(String)

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

app = FastAPI(
    title="Supplier API Playground",
    description="Aplikasi server API sederhana untuk belajar konsep REST API",
    version="1.0.0"
)

fake_users_db = {
    "jen": {
        "username": "jen",
        "hashed_password": PasswordHash.recommended().hash("belajar123")
    }
}

SECRET_KEY = "belajar-api-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if user is None or not password_hash.verify(password, user["hashed_password"]):
        return None
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Token tidak valid atau sudah kedaluwarsa",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception
    user = fake_users_db.get(username)
    if user is None:
        raise credentials_exception
    return user

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Username atau password salah",
            headers={"WWW-Authenticate": "Bearer"}
        )
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

@app.get("/api/suppliers/", response_model=list[SupplierResponse], dependencies=[Depends(get_current_user)])
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

@app.get("/api/suppliers/{supplier_id}", response_model=SupplierResponse, dependencies=[Depends(get_current_user)])
def get_supplier_by_id(supplier_id: int, db: Session = Depends(get_db)):
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier tidak ditemukan")
    return supplier

@app.post("/api/suppliers/", response_model=SupplierResponse, status_code=201, dependencies=[Depends(get_current_user)])
def create_supplier(supplier: SupplierCreate, db: Session = Depends(get_db)):
    supplier_data = supplier.model_dump() if hasattr(supplier, "model_dump") else supplier.dict()
    db_supplier = SupplierDB(**supplier_data)
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier

@app.put("/api/suppliers/{supplier_id}", response_model=SupplierResponse, dependencies=[Depends(get_current_user)])
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

@app.delete("/api/suppliers/{supplier_id}", dependencies=[Depends(get_current_user)])
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)):
    db_supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if db_supplier is None:
        raise HTTPException(status_code=404, detail="Supplier tidak ditemukan")
    db.delete(db_supplier)
    db.commit()
    return {"message": f"Supplier dengan id {supplier_id} berhasil dihapus"}
