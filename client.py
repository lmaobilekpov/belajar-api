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