import httpx

BASE_URL = "http://127.0.0.1:8000"

LOGIN_DATA = {
    "grant_type": "password",
    "username": "jen",
    "password": "belajar123",
}


def login() -> str:
    """Log in to the API and return the access token."""
    response = httpx.post(
        f"{BASE_URL}/token",
        data=LOGIN_DATA,
    )

    print("Login status:", response.status_code)

    token_data = response.json()
    return token_data["access_token"]


def get_headers(access_token: str) -> dict[str, str]:
    """Build the Authorization header for protected requests."""
    return {
        "Authorization": f"Bearer {access_token}",
    }


def get_suppliers(headers: dict[str, str]) -> httpx.Response:
    """Request all suppliers."""
    return httpx.get(
        f"{BASE_URL}/api/suppliers/",
        headers=headers,
    )


def get_supplier_by_id(
    supplier_id: int,
    headers: dict[str, str],
) -> httpx.Response:
    """Request one supplier by its ID."""
    return httpx.get(
        f"{BASE_URL}/api/suppliers/{supplier_id}",
        headers=headers,
    )


def search_suppliers(
    search_term: str,
    headers: dict[str, str],
) -> httpx.Response:
    """Search suppliers using a query parameter."""
    return httpx.get(
        f"{BASE_URL}/api/suppliers/",
        params={"search": search_term},
        headers=headers,
    )


def create_supplier(
    supplier_data: dict[str, str],
    headers: dict[str, str],
) -> httpx.Response:
    """Create a supplier by sending JSON to the API."""
    return httpx.post(
        f"{BASE_URL}/api/suppliers/",
        json=supplier_data,
        headers=headers,
    )


def update_supplier(
    supplier_id: int,
    supplier_data: dict[str, str],
    headers: dict[str, str],
) -> httpx.Response:
    """Update an existing supplier by ID."""
    return httpx.put(
        f"{BASE_URL}/api/suppliers/{supplier_id}",
        json=supplier_data,
        headers=headers,
    )


def delete_supplier(
    supplier_id: int,
    headers: dict[str, str],
) -> httpx.Response:
    """Delete a supplier by ID."""
    return httpx.delete(
        f"{BASE_URL}/api/suppliers/{supplier_id}",
        headers=headers,
    )


def show_response(
    status_label: str,
    data_label: str,
    response: httpx.Response,
) -> None:
    """Print the status code and JSON response body."""
    print(f"{status_label} status:", response.status_code)
    print(f"{data_label}:")
    print(response.json())


def main() -> None:
    access_token = login()
    headers = get_headers(access_token)

    # The default run only reads data, so it is safe to rerun.
    show_response(
        "Supplier API",
        "Supplier data",
        get_suppliers(headers),
    )
    show_response(
        "Supplier detail",
        "Supplier detail",
        get_supplier_by_id(4, headers),
    )
    show_response(
        "Search",
        "Search results",
        search_suppliers("jakarta", headers),
    )


if __name__ == "__main__":
    main()
