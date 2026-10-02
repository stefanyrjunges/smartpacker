# Auth

def test_register_returns_token(client):
    res = client.post("/auth/register", json={
        "email": "new@example.com",
        "password": "password123"
    })

    assert res.status_code == 201
    assert "token" in res.get_json()


def test_register_rejects_short_password(client):
    res = client.post("/auth/register", json={
        "email": "new@example.com",
        "password": "123"
    })

    assert res.status_code == 400


def test_register_rejects_duplicate_email(client):
    client.post("/auth/register", json={"email": "a@example.com", "password": "password123"})
    res = client.post("/auth/register", json={"email": "a@example.com", "password": "password123"})

    assert res.status_code == 409


def test_login_with_correct_password(client):
    client.post("/auth/register", json={"email": "a@example.com", "password": "password123"})
    res = client.post("/auth/login", json={"email": "a@example.com", "password": "password123"})

    assert res.status_code == 200
    assert "token" in res.get_json()


def test_login_with_wrong_password(client):
    client.post("/auth/register", json={"email": "a@example.com", "password": "password123"})
    res = client.post("/auth/login", json={"email": "a@example.com", "password": "wrongpass"})

    assert res.status_code == 401


# Protected routes

def test_trips_require_authentication(client):
    res = client.get("/trips")
    assert res.status_code == 401


def test_create_and_get_trip(client, auth_headers):
    res = client.post("/trips", headers=auth_headers, json={
        "destination": "Rome",
        "luggage_type": "checked",
        "start_date": "2026-06-01",
        "end_date": "2026-06-05"
    })

    assert res.status_code == 201
    trip_id = res.get_json()["id"]

    res = client.get(f"/trips/{trip_id}", headers=auth_headers)
    assert res.status_code == 200
    assert res.get_json()["destination"] == "Rome"


def test_create_trip_with_invalid_dates(client, auth_headers):
    res = client.post("/trips", headers=auth_headers, json={
        "destination": "Rome",
        "luggage_type": "checked",
        "start_date": "2026-06-10",
        "end_date": "2026-06-05"
    })

    assert res.status_code == 400


def test_users_only_see_their_own_trips(client):
    # First user creates a trip
    res = client.post("/auth/register", json={"email": "user1@example.com", "password": "password123"})
    user1_headers = {"Authorization": f"Bearer {res.get_json()['token']}"}

    create = client.post("/trips", headers=user1_headers, json={
        "destination": "Lisbon",
        "luggage_type": "checked",
        "start_date": "2026-06-01",
        "end_date": "2026-06-05"
    })
    trip_id = create.get_json()["id"]

    # Second user should not see or access it
    res = client.post("/auth/register", json={"email": "user2@example.com", "password": "password123"})
    user2_headers = {"Authorization": f"Bearer {res.get_json()['token']}"}

    all_trips = client.get("/trips", headers=user2_headers)
    assert all_trips.get_json() == []

    direct = client.get(f"/trips/{trip_id}", headers=user2_headers)
    assert direct.status_code == 404


def test_delete_trip(client, auth_headers):
    create = client.post("/trips", headers=auth_headers, json={
        "destination": "Rome",
        "luggage_type": "checked",
        "start_date": "2026-06-01",
        "end_date": "2026-06-05"
    })
    trip_id = create.get_json()["id"]

    res = client.delete(f"/trips/{trip_id}", headers=auth_headers)
    assert res.status_code == 200

    res = client.get(f"/trips/{trip_id}", headers=auth_headers)
    assert res.status_code == 404


def test_add_and_get_activities(client, auth_headers):
    create = client.post("/trips", headers=auth_headers, json={
        "destination": "Rome",
        "luggage_type": "checked",
        "start_date": "2026-06-01",
        "end_date": "2026-06-05"
    })
    trip_id = create.get_json()["id"]

    res = client.post(f"/trips/{trip_id}/activities", headers=auth_headers, json={
        "activities": ["hiking", "swimming"]
    })
    assert res.status_code == 201

    res = client.get(f"/trips/{trip_id}/activities", headers=auth_headers)
    activities = res.get_json()
    assert len(activities) == 2


def test_add_custom_packing_item(client, auth_headers):
    create = client.post("/trips", headers=auth_headers, json={
        "destination": "Rome",
        "luggage_type": "checked",
        "start_date": "2026-06-01",
        "end_date": "2026-06-05"
    })
    trip_id = create.get_json()["id"]

    res = client.post(f"/trips/{trip_id}/packing-list", headers=auth_headers, json={
        "name": "Travel adapter",
        "quantity": 1
    })

    assert res.status_code == 201
    assert res.get_json()["name"] == "Travel adapter"
    assert res.get_json()["category"] == "Other"
