import httpx

BASE_URL = "http://127.0.0.1:8000"

login_data = {
    "grant_type": "password",
    "username": "jen",
    "password": "belajar123",
}

login_response = httpx.post(
    f"{BASE_URL}/token",
    data=login_data
)

print("Login status:", login_response.status_code)

token_data = login_response.json()
access_token = token_data["access_token"]

headers = {
    "Authorization": f"Bearer {access_token}"
}

suppliers_response = httpx.get(
    f"{BASE_URL}/api/suppliers/",
    headers=headers
)

print("Supplier API status:", suppliers_response.status_code)
print("Supplier data:")
print(suppliers_response.json())


supplier_id = 4

supplier_detail_response = httpx.get(
    f"{BASE_URL}/api/suppliers/{supplier_id}",
    headers=headers
)

print("Supplier detail status:", supplier_detail_response.status_code)
print("Supplier detail:")
print(supplier_detail_response.json())

search_response = httpx.get(
    f"{BASE_URL}/api/suppliers/",
    params={"search": "jakarta"},
    headers=headers
)

print("Search status:", search_response.status_code)
print("Search results:")
print(search_response.json())

new_supplier_data = {
    "kode_supplier": "SUP005",
    "nama_supplier": "PT Contoh",
    "alamat": "Depok"
}

# new_supplier_response = httpx.post(
   # f"{BASE_URL}/api/suppliers/",
    #json=new_supplier_data,
    #headers=headers
#)

#print("Create supplier status:", new_supplier_response.status_code)
#print("Created supplier:")
#print(new_supplier_response.json())

update_supplier_id = 5

updated_supplier_data = {
    "kode_supplier": "SUP005",
    "nama_supplier": "PT Contoh Indonesia",
    "alamat": "Depok Barat"
}

update_response = httpx.put(
    f"{BASE_URL}/api/suppliers/{update_supplier_id}",
    json=updated_supplier_data,
    headers=headers
)

print("Update supplier status:", update_response.status_code)
print("Updated supplier:")
print(update_response.json())