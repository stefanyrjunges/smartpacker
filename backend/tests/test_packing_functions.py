import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from packing_functions import generate_packing_list


# Small stand-ins so we can test the logic without the database
class FakeTrip:
    def __init__(self, start_date, end_date, luggage_type="checked"):
        self.start_date = start_date
        self.end_date = end_date
        self.luggage_type = luggage_type


class FakeActivity:
    def __init__(self, activity):
        self.activity = activity


# Mild weather that triggers no weather-based items, so tests stay predictable
mild_weather = {
    "rain_expected": False,
    "min_temperature": 15,
    "max_temperature": 18,
    "total_precipitation": 0
}


def get_item(result, name):
    for item in result["items"]:
        if item["name"] == name:
            return item
    return None


def test_duration_sets_basic_clothing_quantity():
    trip = FakeTrip(date(2026, 6, 1), date(2026, 6, 4))  # 4 days
    result = generate_packing_list(trip, [], mild_weather)

    assert result["duration"] == 4
    assert get_item(result, "T-shirts")["quantity"] == 4
    assert get_item(result, "Socks")["quantity"] == 4
    assert get_item(result, "Underwear")["quantity"] == 4


def test_single_day_trip():
    trip = FakeTrip(date(2026, 6, 1), date(2026, 6, 1))  # same day = 1 day
    result = generate_packing_list(trip, [], mild_weather)

    assert result["duration"] == 1
    assert get_item(result, "T-shirts")["quantity"] == 1


def test_rain_adds_rain_items():
    trip = FakeTrip(date(2026, 6, 1), date(2026, 6, 3))
    weather = {"rain_expected": True, "min_temperature": 15, "max_temperature": 18, "total_precipitation": 5}

    result = generate_packing_list(trip, [], weather)

    assert get_item(result, "Rain jacket") is not None
    assert get_item(result, "Umbrella") is not None


def test_cold_temperature_adds_warm_items():
    trip = FakeTrip(date(2026, 1, 1), date(2026, 1, 3))
    weather = {"rain_expected": False, "min_temperature": 2, "max_temperature": 6, "total_precipitation": 0}

    result = generate_packing_list(trip, [], weather)

    assert get_item(result, "Warm jacket") is not None
    assert get_item(result, "Scarf") is not None
    # Below 5 degrees should also add gloves
    assert get_item(result, "Gloves") is not None


def test_warm_temperature_adds_summer_items():
    trip = FakeTrip(date(2026, 7, 1), date(2026, 7, 3))
    weather = {"rain_expected": False, "min_temperature": 18, "max_temperature": 25, "total_precipitation": 0}

    result = generate_packing_list(trip, [], weather)

    assert get_item(result, "Sunscreen") is not None
    assert get_item(result, "Sunglasses") is not None


def test_activity_adds_relevant_items():
    trip = FakeTrip(date(2026, 6, 1), date(2026, 6, 3))
    activities = [FakeActivity("hiking")]

    result = generate_packing_list(trip, activities, mild_weather)

    assert get_item(result, "Hiking boots") is not None
    assert get_item(result, "Water bottle") is not None


def test_activity_matching_is_case_insensitive():
    trip = FakeTrip(date(2026, 6, 1), date(2026, 6, 3))
    activities = [FakeActivity("HIKING")]

    result = generate_packing_list(trip, activities, mild_weather)

    assert get_item(result, "Hiking boots") is not None


def test_multiple_activities_do_not_duplicate_items():
    trip = FakeTrip(date(2026, 6, 1), date(2026, 6, 3))
    # Both include "Water bottle"
    activities = [FakeActivity("hiking"), FakeActivity("camping")]

    result = generate_packing_list(trip, activities, mild_weather)

    water_bottles = [i for i in result["items"] if i["name"] == "Water bottle"]
    assert len(water_bottles) == 1


def test_unknown_activity_is_ignored():
    trip = FakeTrip(date(2026, 6, 1), date(2026, 6, 3))
    activities = [FakeActivity("underwater basket weaving")]

    result = generate_packing_list(trip, activities, mild_weather)

    # Should still produce the basic list without crashing
    assert get_item(result, "T-shirts") is not None


def test_carry_on_caps_clothing_quantity():
    trip = FakeTrip(date(2026, 6, 1), date(2026, 6, 10), luggage_type="carry-on")  # 10 days
    result = generate_packing_list(trip, [], mild_weather)

    # Without the cap this would be 10, carry-on caps it at 5
    assert get_item(result, "T-shirts")["quantity"] == 5
    assert get_item(result, "Underwear")["quantity"] == 5


def test_backpack_caps_clothing_quantity():
    trip = FakeTrip(date(2026, 6, 1), date(2026, 6, 10), luggage_type="backpack")
    result = generate_packing_list(trip, [], mild_weather)

    assert get_item(result, "T-shirts")["quantity"] == 5


def test_checked_bag_does_not_cap_quantity():
    trip = FakeTrip(date(2026, 6, 1), date(2026, 6, 10), luggage_type="checked")  # 10 days
    result = generate_packing_list(trip, [], mild_weather)

    # Checked bag has no cap, so it stays at the full duration
    assert get_item(result, "T-shirts")["quantity"] == 10
