import asyncio
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import (
    HTTPBasic,
    HTTPBasicCredentials,
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pwdlib import PasswordHash
from sqlalchemy import Boolean, Column, Date, Integer, String, create_engine, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./suppliers.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))


# ---------------------------------------------------------------------------
# Database models: all records in this playground are training/demo records.
# ---------------------------------------------------------------------------
class SupplierDB(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    kode_supplier = Column(String, unique=True, index=True, nullable=False)
    nama_supplier = Column(String, nullable=False)
    alamat = Column(String, nullable=False)


class EmployeeDB(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    kode_karyawan = Column(String, unique=True, index=True, nullable=False)
    nama_lengkap = Column(String, nullable=False)
    jabatan = Column(String, nullable=False)
    tanggal_lahir = Column(Date, nullable=False)
    aktif = Column(Boolean, default=True, nullable=False)


# ---------------------------------------------------------------------------
# API request/response schemas.
# ---------------------------------------------------------------------------
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


class EmployeeBase(BaseModel):
    kode_karyawan: str
    nama_lengkap: str
    jabatan: str
    tanggal_lahir: date
    aktif: bool = True


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeResponse(EmployeeBase):
    id: int

    class Config:
        from_attributes = True


app = FastAPI(
    title="Master Data API Playground",
    description=(
        "Aplikasi latihan untuk mengelola data dummy karyawan dan supplier "
        "serta menyediakan API bagi aplikasi konsumen."
    ),
    version="1.0.0",
)

fake_users_db = {
    "jen": {
        "username": "jen",
        "hashed_password": PasswordHash.recommended().hash("belajar123"),
    }
}

SECRET_KEY = "belajar-api-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
web_security = HTTPBasic()


def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if user is None or not password_hash.verify(password, user["hashed_password"]):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=15)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Token tidak valid atau sudah kedaluwarsa",
        headers={"WWW-Authenticate": "Bearer"},
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


def require_web_user(
    credentials: HTTPBasicCredentials = Depends(web_security),
):
    """Protect the local training UI with the playground account."""
    user = authenticate_user(credentials.username, credentials.password)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Username atau password salah",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user


@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Username atau password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
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
    try:
        if db.query(SupplierDB).count() == 0:
            db.add_all(
                [
                    SupplierDB(
                        kode_supplier="SUP001",
                        nama_supplier="PT Maju Jaya",
                        alamat="Jakarta",
                    ),
                    SupplierDB(
                        kode_supplier="SUP002",
                        nama_supplier="PT Sumber Makmur",
                        alamat="Depok",
                    ),
                    SupplierDB(
                        kode_supplier="SUP003",
                        nama_supplier="CV Berkah Abadi",
                        alamat="Bogor",
                    ),
                ]
            )

        if db.query(EmployeeDB).count() == 0:
            db.add_all(
                [
                    EmployeeDB(
                        kode_karyawan="KRY-DEMO-001",
                        nama_lengkap="Budi Karyawan Uji",
                        jabatan="Petugas Uji 1",
                        tanggal_lahir=date(1990, 1, 10),
                        aktif=True,
                    ),
                    EmployeeDB(
                        kode_karyawan="KRY-DEMO-002",
                        nama_lengkap="Siti Karyawan Uji",
                        jabatan="Petugas Uji 2",
                        tanggal_lahir=date(1992, 5, 20),
                        aktif=True,
                    ),
                    EmployeeDB(
                        kode_karyawan="KRY-DEMO-003",
                        nama_lengkap="Andi Karyawan Uji",
                        jabatan="Petugas Uji 3",
                        tanggal_lahir=date(1988, 9, 15),
                        aktif=False,
                    ),
                ]
            )

        db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Local web UI: open http://127.0.0.1:8000/web/ in the browser.
# The UI is for local training only, not a production administration site.
# ---------------------------------------------------------------------------
@app.get("/web/", response_class=HTMLResponse)
def web_home(
    request: Request,
    db: Session = Depends(get_db),
    _user=Depends(require_web_user),
):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "employee_count": db.query(EmployeeDB).count(),
            "supplier_count": db.query(SupplierDB).count(),
        },
    )


@app.get("/web/suppliers/", response_class=HTMLResponse)
def web_supplier_list(
    request: Request,
    db: Session = Depends(get_db),
    _user=Depends(require_web_user),
):
    suppliers = db.query(SupplierDB).order_by(SupplierDB.nama_supplier).all()
    rows = [
        {
            "values": [item.id, item.kode_supplier, item.nama_supplier, item.alamat],
            "edit_url": f"/web/suppliers/{item.id}/edit",
            "delete_url": f"/web/suppliers/{item.id}/delete",
            "label": item.nama_supplier,
        }
        for item in suppliers
    ]
    return templates.TemplateResponse(
        request=request,
        name="list.html",
        context={
            "title": "Data Supplier Dummy",
            "description": "Data latihan yang disediakan oleh Master Data API.",
            "columns": ["ID API", "Kode Supplier", "Nama Supplier", "Alamat"],
            "rows": rows,
            "add_url": "/web/suppliers/new",
        },
    )


def supplier_form_fields(values=None):
    values = values or {}
    return [
        {
            "name": "kode_supplier",
            "label": "Kode supplier",
            "value": values.get("kode_supplier", ""),
            "type": "text",
            "required": True,
        },
        {
            "name": "nama_supplier",
            "label": "Nama supplier",
            "value": values.get("nama_supplier", ""),
            "type": "text",
            "required": True,
        },
        {
            "name": "alamat",
            "label": "Alamat",
            "value": values.get("alamat", ""),
            "type": "text",
            "required": True,
        },
    ]


@app.get("/web/suppliers/new", response_class=HTMLResponse)
def web_supplier_new_form(
    request: Request,
    _user=Depends(require_web_user),
):
    return templates.TemplateResponse(
        request=request,
        name="form.html",
        context={
            "title": "Tambah Supplier Dummy",
            "description": "Tambahkan supplier fiktif untuk latihan API.",
            "fields": supplier_form_fields(),
            "action_url": "/web/suppliers/new",
            "submit_label": "Simpan supplier",
        },
    )


@app.post("/web/suppliers/new", response_class=HTMLResponse)
def web_supplier_create(
    request: Request,
    kode_supplier: Annotated[str, Form()],
    nama_supplier: Annotated[str, Form()],
    alamat: Annotated[str, Form()],
    db: Session = Depends(get_db),
    _user=Depends(require_web_user),
):
    values = {
        "kode_supplier": kode_supplier.strip(),
        "nama_supplier": nama_supplier.strip(),
        "alamat": alamat.strip(),
    }
    error = None
    if not all(values.values()):
        error = "Semua field wajib diisi."
    else:
        db.add(SupplierDB(**values))
        try:
            db.commit()
            return RedirectResponse("/web/suppliers/", status_code=303)
        except IntegrityError:
            db.rollback()
            error = "Kode supplier sudah digunakan. Gunakan kode dummy yang berbeda."

    return templates.TemplateResponse(
        request=request,
        name="form.html",
        status_code=400,
        context={
            "title": "Tambah Supplier Dummy",
            "description": "Tambahkan supplier fiktif untuk latihan API.",
            "fields": supplier_form_fields(values),
            "action_url": "/web/suppliers/new",
            "submit_label": "Simpan supplier",
            "error": error,
        },
    )


@app.get("/web/suppliers/{supplier_id}/edit", response_class=HTMLResponse)
def web_supplier_edit_form(
    supplier_id: int,
    request: Request,
    db: Session = Depends(get_db),
    _user=Depends(require_web_user),
):
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier tidak ditemukan")
    values = {
        "kode_supplier": supplier.kode_supplier,
        "nama_supplier": supplier.nama_supplier,
        "alamat": supplier.alamat,
    }
    return templates.TemplateResponse(
        request=request,
        name="form.html",
        context={
            "title": "Edit Supplier Dummy",
            "description": "Ubah data latihan untuk menguji proses sinkronisasi.",
            "fields": supplier_form_fields(values),
            "action_url": f"/web/suppliers/{supplier.id}/edit",
            "submit_label": "Simpan perubahan",
        },
    )


@app.post("/web/suppliers/{supplier_id}/edit", response_class=HTMLResponse)
def web_supplier_update(
    supplier_id: int,
    request: Request,
    kode_supplier: Annotated[str, Form()],
    nama_supplier: Annotated[str, Form()],
    alamat: Annotated[str, Form()],
    db: Session = Depends(get_db),
    _user=Depends(require_web_user),
):
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier tidak ditemukan")

    values = {
        "kode_supplier": kode_supplier.strip(),
        "nama_supplier": nama_supplier.strip(),
        "alamat": alamat.strip(),
    }
    error = None
    if not all(values.values()):
        error = "Semua field wajib diisi."
    else:
        for field, value in values.items():
            setattr(supplier, field, value)
        try:
            db.commit()
            return RedirectResponse("/web/suppliers/", status_code=303)
        except IntegrityError:
            db.rollback()
            error = "Kode supplier sudah digunakan oleh supplier lain."

    return templates.TemplateResponse(
        request=request,
        name="form.html",
        status_code=400,
        context={
            "title": "Edit Supplier Dummy",
            "description": "Ubah data latihan untuk menguji proses sinkronisasi.",
            "fields": supplier_form_fields(values),
            "action_url": f"/web/suppliers/{supplier_id}/edit",
            "submit_label": "Simpan perubahan",
            "error": error,
        },
    )


@app.post("/web/suppliers/{supplier_id}/delete")
def web_supplier_delete(
    supplier_id: int,
    db: Session = Depends(get_db),
    _user=Depends(require_web_user),
):
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier tidak ditemukan")
    db.delete(supplier)
    db.commit()
    return RedirectResponse("/web/suppliers/", status_code=303)


@app.get("/web/employees/", response_class=HTMLResponse)
def web_employee_list(
    request: Request,
    db: Session = Depends(get_db),
    _user=Depends(require_web_user),
):
    employees = db.query(EmployeeDB).order_by(EmployeeDB.nama_lengkap).all()
    rows = [
        {
            "values": [
                item.id,
                item.kode_karyawan,
                item.nama_lengkap,
                item.jabatan,
                item.tanggal_lahir.isoformat(),
                "Aktif" if item.aktif else "Tidak aktif",
            ],
            "edit_url": f"/web/employees/{item.id}/edit",
            "delete_url": f"/web/employees/{item.id}/delete",
            "label": item.nama_lengkap,
        }
        for item in employees
    ]
    return templates.TemplateResponse(
        request=request,
        name="list.html",
        context={
            "title": "Data Karyawan Dummy",
            "description": "Semua record berikut adalah data fiktif untuk latihan.",
            "columns": [
                "ID API",
                "Kode Karyawan",
                "Nama Lengkap",
                "Jabatan",
                "Tanggal Lahir",
                "Status",
            ],
            "rows": rows,
            "add_url": "/web/employees/new",
        },
    )


def employee_form_fields(values=None):
    values = values or {}
    return [
        {
            "name": "kode_karyawan",
            "label": "Kode karyawan",
            "value": values.get("kode_karyawan", ""),
            "type": "text",
            "required": True,
        },
        {
            "name": "nama_lengkap",
            "label": "Nama lengkap",
            "value": values.get("nama_lengkap", ""),
            "type": "text",
            "required": True,
        },
        {
            "name": "jabatan",
            "label": "Jabatan",
            "value": values.get("jabatan", ""),
            "type": "text",
            "required": True,
        },
        {
            "name": "tanggal_lahir",
            "label": "Tanggal lahir",
            "value": values.get("tanggal_lahir", ""),
            "type": "date",
            "required": True,
        },
        {
            "name": "aktif",
            "label": "Karyawan aktif",
            "value": "true",
            "type": "checkbox",
            "checked": str(values.get("aktif", True)).lower() in ("true", "on", "1"),
            "required": False,
        },
    ]


@app.get("/web/employees/new", response_class=HTMLResponse)
def web_employee_new_form(
    request: Request,
    _user=Depends(require_web_user),
):
    return templates.TemplateResponse(
        request=request,
        name="form.html",
        context={
            "title": "Tambah Karyawan Dummy",
            "description": "Gunakan identitas dan nama fiktif, bukan data karyawan kantor.",
            "fields": employee_form_fields(),
            "action_url": "/web/employees/new",
            "submit_label": "Simpan karyawan",
        },
    )


@app.post("/web/employees/new", response_class=HTMLResponse)
def web_employee_create(
    request: Request,
    kode_karyawan: Annotated[str, Form()],
    nama_lengkap: Annotated[str, Form()],
    jabatan: Annotated[str, Form()],
    tanggal_lahir: Annotated[str, Form()],
    aktif: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
    _user=Depends(require_web_user),
):
    values = {
        "kode_karyawan": kode_karyawan.strip(),
        "nama_lengkap": nama_lengkap.strip(),
        "jabatan": jabatan.strip(),
        "tanggal_lahir": tanggal_lahir.strip(),
        "aktif": aktif is not None,
    }
    error = None
    try:
        birth_date = date.fromisoformat(values["tanggal_lahir"])
    except ValueError:
        birth_date = None
        error = "Tanggal lahir tidak valid."

    if not all([values["kode_karyawan"], values["nama_lengkap"], values["jabatan"]]):
        error = "Kode, nama, dan jabatan wajib diisi."

    if error is None and birth_date:
        db.add(
            EmployeeDB(
                kode_karyawan=values["kode_karyawan"],
                nama_lengkap=values["nama_lengkap"],
                jabatan=values["jabatan"],
                tanggal_lahir=birth_date,
                aktif=values["aktif"],
            )
        )
        try:
            db.commit()
            return RedirectResponse("/web/employees/", status_code=303)
        except IntegrityError:
            db.rollback()
            error = "Kode karyawan sudah digunakan. Gunakan kode dummy yang berbeda."

    return templates.TemplateResponse(
        request=request,
        name="form.html",
        status_code=400,
        context={
            "title": "Tambah Karyawan Dummy",
            "description": "Gunakan identitas dan nama fiktif, bukan data karyawan kantor.",
            "fields": employee_form_fields(values),
            "action_url": "/web/employees/new",
            "submit_label": "Simpan karyawan",
            "error": error,
        },
    )


@app.get("/web/employees/{employee_id}/edit", response_class=HTMLResponse)
def web_employee_edit_form(
    employee_id: int,
    request: Request,
    db: Session = Depends(get_db),
    _user=Depends(require_web_user),
):
    employee = db.query(EmployeeDB).filter(EmployeeDB.id == employee_id).first()
    if employee is None:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")
    values = {
        "kode_karyawan": employee.kode_karyawan,
        "nama_lengkap": employee.nama_lengkap,
        "jabatan": employee.jabatan,
        "tanggal_lahir": employee.tanggal_lahir.isoformat(),
        "aktif": employee.aktif,
    }
    return templates.TemplateResponse(
        request=request,
        name="form.html",
        context={
            "title": "Edit Karyawan Dummy",
            "description": "Ubah data fiktif untuk menguji proses sinkronisasi.",
            "fields": employee_form_fields(values),
            "action_url": f"/web/employees/{employee.id}/edit",
            "submit_label": "Simpan perubahan",
        },
    )


@app.post("/web/employees/{employee_id}/edit", response_class=HTMLResponse)
def web_employee_update(
    employee_id: int,
    request: Request,
    kode_karyawan: Annotated[str, Form()],
    nama_lengkap: Annotated[str, Form()],
    jabatan: Annotated[str, Form()],
    tanggal_lahir: Annotated[str, Form()],
    aktif: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
    _user=Depends(require_web_user),
):
    employee = db.query(EmployeeDB).filter(EmployeeDB.id == employee_id).first()
    if employee is None:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")

    values = {
        "kode_karyawan": kode_karyawan.strip(),
        "nama_lengkap": nama_lengkap.strip(),
        "jabatan": jabatan.strip(),
        "tanggal_lahir": tanggal_lahir.strip(),
        "aktif": aktif is not None,
    }
    error = None
    try:
        birth_date = date.fromisoformat(values["tanggal_lahir"])
    except ValueError:
        birth_date = None
        error = "Tanggal lahir tidak valid."

    if not all([values["kode_karyawan"], values["nama_lengkap"], values["jabatan"]]):
        error = "Kode, nama, dan jabatan wajib diisi."

    if error is None and birth_date:
        employee.kode_karyawan = values["kode_karyawan"]
        employee.nama_lengkap = values["nama_lengkap"]
        employee.jabatan = values["jabatan"]
        employee.tanggal_lahir = birth_date
        employee.aktif = values["aktif"]
        try:
            db.commit()
            return RedirectResponse("/web/employees/", status_code=303)
        except IntegrityError:
            db.rollback()
            error = "Kode karyawan sudah digunakan oleh karyawan lain."

    return templates.TemplateResponse(
        request=request,
        name="form.html",
        status_code=400,
        context={
            "title": "Edit Karyawan Dummy",
            "description": "Ubah data fiktif untuk menguji proses sinkronisasi.",
            "fields": employee_form_fields(values),
            "action_url": f"/web/employees/{employee_id}/edit",
            "submit_label": "Simpan perubahan",
            "error": error,
        },
    )


@app.post("/web/employees/{employee_id}/delete")
def web_employee_delete(
    employee_id: int,
    db: Session = Depends(get_db),
    _user=Depends(require_web_user),
):
    employee = db.query(EmployeeDB).filter(EmployeeDB.id == employee_id).first()
    if employee is None:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")
    db.delete(employee)
    db.commit()
    return RedirectResponse("/web/employees/", status_code=303)


# ---------------------------------------------------------------------------
# Protected supplier API.
# ---------------------------------------------------------------------------
@app.get(
    "/api/suppliers/",
    response_model=list[SupplierResponse],
    dependencies=[Depends(get_current_user)],
)
def get_all_suppliers(search: str | None = None, db: Session = Depends(get_db)):
    query = db.query(SupplierDB)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                SupplierDB.kode_supplier.ilike(search_pattern),
                SupplierDB.nama_supplier.ilike(search_pattern),
                SupplierDB.alamat.ilike(search_pattern),
            )
        )
    return query.all()


@app.get(
    "/api/suppliers/{supplier_id}",
    response_model=SupplierResponse,
    dependencies=[Depends(get_current_user)],
)
def get_supplier_by_id(supplier_id: int, db: Session = Depends(get_db)):
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier tidak ditemukan")
    return supplier


@app.post(
    "/api/suppliers/",
    response_model=SupplierResponse,
    status_code=201,
    dependencies=[Depends(get_current_user)],
)
def create_supplier(supplier: SupplierCreate, db: Session = Depends(get_db)):
    db_supplier = SupplierDB(**supplier.model_dump())
    db.add(db_supplier)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Kode supplier sudah digunakan")
    db.refresh(db_supplier)
    return db_supplier


@app.put(
    "/api/suppliers/{supplier_id}",
    response_model=SupplierResponse,
    dependencies=[Depends(get_current_user)],
)
def update_supplier(
    supplier_id: int,
    supplier_update: SupplierCreate,
    db: Session = Depends(get_db),
):
    db_supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if db_supplier is None:
        raise HTTPException(status_code=404, detail="Supplier tidak ditemukan")

    for key, value in supplier_update.model_dump().items():
        setattr(db_supplier, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Kode supplier sudah digunakan")
    db.refresh(db_supplier)
    return db_supplier


@app.delete(
    "/api/suppliers/{supplier_id}",
    dependencies=[Depends(get_current_user)],
)
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)):
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier tidak ditemukan")
    db.delete(supplier)
    db.commit()
    return {"message": f"Supplier dengan id {supplier_id} berhasil dihapus"}


# ---------------------------------------------------------------------------
# Protected employee API.
# ---------------------------------------------------------------------------
@app.get(
    "/api/employees/",
    response_model=list[EmployeeResponse],
    dependencies=[Depends(get_current_user)],
)
def get_all_employees(search: str | None = None, db: Session = Depends(get_db)):
    query = db.query(EmployeeDB)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                EmployeeDB.kode_karyawan.ilike(search_pattern),
                EmployeeDB.nama_lengkap.ilike(search_pattern),
                EmployeeDB.jabatan.ilike(search_pattern),
            )
        )
    return query.order_by(EmployeeDB.id).all()


@app.get(
    "/api/employees/{employee_id}",
    response_model=EmployeeResponse,
    dependencies=[Depends(get_current_user)],
)
def get_employee_by_id(employee_id: int, db: Session = Depends(get_db)):
    employee = db.query(EmployeeDB).filter(EmployeeDB.id == employee_id).first()
    if employee is None:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")
    return employee


@app.post(
    "/api/employees/",
    response_model=EmployeeResponse,
    status_code=201,
    dependencies=[Depends(get_current_user)],
)
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    db_employee = EmployeeDB(**employee.model_dump())
    db.add(db_employee)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Kode karyawan sudah digunakan")
    db.refresh(db_employee)
    return db_employee


@app.put(
    "/api/employees/{employee_id}",
    response_model=EmployeeResponse,
    dependencies=[Depends(get_current_user)],
)
def update_employee(
    employee_id: int,
    employee_update: EmployeeCreate,
    db: Session = Depends(get_db),
):
    db_employee = db.query(EmployeeDB).filter(EmployeeDB.id == employee_id).first()
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")

    for key, value in employee_update.model_dump().items():
        setattr(db_employee, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Kode karyawan sudah digunakan")
    db.refresh(db_employee)
    return db_employee


@app.delete(
    "/api/employees/{employee_id}",
    dependencies=[Depends(get_current_user)],
)
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    employee = db.query(EmployeeDB).filter(EmployeeDB.id == employee_id).first()
    if employee is None:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")
    db.delete(employee)
    db.commit()
    return {"message": f"Karyawan dengan id {employee_id} berhasil dihapus"}


@app.get("/test-timeout")
async def test_timeout():
    """Endpoint latihan yang sengaja menunggu sebelum memberi response."""
    await asyncio.sleep(6)
    return {"message": "Server selesai menunggu selama 6 detik."}
