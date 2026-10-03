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


def test_weather_returns_cached_data_without_calling_api(client, auth_headers):
    from flask_app import db
    from database.models import WeatherCache

    create = client.post("/trips", headers=auth_headers, json={
        "destination": "Rome",
        "luggage_type": "checked",
        "start_date": "2026-06-01",
        "end_date": "2026-06-05"
    })
    trip_id = create.get_json()["id"]

    # Pre-save weather so the endpoint should return it instead of calling the API
    db.session.add(WeatherCache(
        destination="Rome",
        country="Italy",
        min_temperature=12.0,
        max_temperature=25.0,
        total_precipitation=0.0,
        rain_expected=False,
        trip_id=trip_id
    ))
    db.session.commit()

    res = client.get(f"/trips/{trip_id}/weather", headers=auth_headers)

    assert res.status_code == 200
    data = res.get_json()
    assert data["destination"] == "Rome"
    assert data["max_temperature"] == 25.0
    assert data["rain_expected"] is False


# CRUD

def test_update_trip(client, auth_headers):
    create = client.post("/trips", headers=auth_headers, json={
        "destination": "Rome",
        "luggage_type": "checked",
        "start_date": "2026-06-01",
        "end_date": "2026-06-05"
    })
    trip_id = create.get_json()["id"]

    res = client.put(f"/trips/{trip_id}", headers=auth_headers, json={
        "destination": "Milan",
        "luggage_type": "carry-on",
        "start_date": "2026-07-01",
        "end_date": "2026-07-04"
    })

    assert res.status_code == 200
    data = res.get_json()
    assert data["destination"] == "Milan"
    assert data["luggage_type"] == "carry-on"

    # The change should have been saved to the database
    res = client.get(f"/trips/{trip_id}", headers=auth_headers)
    assert res.get_json()["destination"] == "Milan"


def test_update_trip_rejects_invalid_luggage(client, auth_headers):
    create = client.post("/trips", headers=auth_headers, json={
        "destination": "Rome",
        "luggage_type": "checked",
        "start_date": "2026-06-01",
        "end_date": "2026-06-05"
    })
    trip_id = create.get_json()["id"]

    res = client.put(f"/trips/{trip_id}", headers=auth_headers, json={
        "destination": "Rome",
        "luggage_type": "suitcase-with-wheels",
        "start_date": "2026-06-01",
        "end_date": "2026-06-05"
    })

    assert res.status_code == 400


# Activities

def test_delete_activity(client, auth_headers):
    create = client.post("/trips", headers=auth_headers, json={
        "destination": "Rome",
        "luggage_type": "checked",
        "start_date": "2026-06-01",
        "end_date": "2026-06-05"
    })
    trip_id = create.get_json()["id"]

    client.post(f"/trips/{trip_id}/activities", headers=auth_headers, json={
        "activities": ["hiking"]
    })
    activity_id = client.get(f"/trips/{trip_id}/activities", headers=auth_headers).get_json()[0]["id"]

    res = client.delete(f"/trips/{trip_id}/activities/{activity_id}", headers=auth_headers)
    assert res.status_code == 200

    remaining = client.get(f"/trips/{trip_id}/activities", headers=auth_headers).get_json()
    assert remaining == []


# Packing items

def test_toggle_packing_item_packed(client, auth_headers):
    create = client.post("/trips", headers=auth_headers, json={
        "destination": "Rome",
        "luggage_type": "checked",
        "start_date": "2026-06-01",
        "end_date": "2026-06-05"
    })
    trip_id = create.get_json()["id"]

    item = client.post(f"/trips/{trip_id}/packing-list", headers=auth_headers, json={
        "name": "Travel adapter",
        "quantity": 1
    }).get_json()

    res = client.patch(f"/trips/{trip_id}/packing-list/{item['id']}", headers=auth_headers, json={
        "packed": True
    })

    assert res.status_code == 200
    assert res.get_json()["packed"] is True


def test_delete_packing_item(client, auth_headers):
    create = client.post("/trips", headers=auth_headers, json={
        "destination": "Rome",
        "luggage_type": "checked",
        "start_date": "2026-06-01",
        "end_date": "2026-06-05"
    })
    trip_id = create.get_json()["id"]

    item = client.post(f"/trips/{trip_id}/packing-list", headers=auth_headers, json={
        "name": "Travel adapter",
        "quantity": 1
    }).get_json()

    res = client.delete(f"/trips/{trip_id}/packing-list/{item['id']}", headers=auth_headers)
    assert res.status_code == 200


# Weather

def _fake_weather_success(destination, start_date, end_date):
    return {
        "destination": "Rome",
        "country": "Italy",
        "min_temperature": 12.0,
        "max_temperature": 25.0,
        "total_precipitation": 0.0,
        "rain_expected": False
    }


def _fake_weather_error(destination, start_date, end_date):
    return {"error": "Destination not found. Please check the spelling and try again."}


def test_weather_returns_error_when_api_fails(client, auth_headers, monkeypatch):
    import flask_app
    monkeypatch.setattr(flask_app, "get_weather", _fake_weather_error)

    create = client.post("/trips", headers=auth_headers, json={
        "destination": "Nowhereville",
        "luggage_type": "checked",
        "start_date": "2026-06-01",
        "end_date": "2026-06-05"
    })
    trip_id = create.get_json()["id"]

    res = client.get(f"/trips/{trip_id}/weather", headers=auth_headers)

    assert res.status_code == 400
    assert "error" in res.get_json()


def test_weather_cache_miss_fetches_then_reuses(client, auth_headers, monkeypatch):
    import flask_app

    calls = {"count": 0}

    def counting_fetch(destination, start_date, end_date):
        calls["count"] += 1
        return _fake_weather_success(destination, start_date, end_date)

    monkeypatch.setattr(flask_app, "get_weather", counting_fetch)

    create = client.post("/trips", headers=auth_headers, json={
        "destination": "Rome",
        "luggage_type": "checked",
        "start_date": "2026-06-01",
        "end_date": "2026-06-05"
    })
    trip_id = create.get_json()["id"]

    # In the first call, the cache is empty so the API will be called and the result stored
    first = client.get(f"/trips/{trip_id}/weather", headers=auth_headers)
    assert first.status_code == 200
    assert calls["count"] == 1

    # The second needs to come from the cache, so the API isn't called again
    second = client.get(f"/trips/{trip_id}/weather", headers=auth_headers)
    assert second.status_code == 200
    assert calls["count"] == 1
