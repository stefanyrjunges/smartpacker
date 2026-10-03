import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trip_functions import validate_data, validate_activities


# Validate data

def test_valid_trip_data():
    data = {
        "destination": "Paris",
        "luggage_type": "checked",
        "start_date": "2026-06-01",
        "end_date": "2026-06-05"
    }
    trip_data, error = validate_data(data)

    assert error is None
    assert trip_data["destination"] == "Paris"
    assert trip_data["start_date"] == date(2026, 6, 1)
    assert trip_data["end_date"] == date(2026, 6, 5)


def test_missing_fields_returns_error():
    data = {"destination": "Paris"}
    trip_data, error = validate_data(data)

    assert trip_data is None
    assert error == "Please fill in all the information"


def test_empty_destination_returns_error():
    data = {
        "destination": "   ",
        "luggage_type": "checked",
        "start_date": "2026-06-01",
        "end_date": "2026-06-05"
    }
    trip_data, error = validate_data(data)

    assert trip_data is None
    assert error == "Please fill in all the information"


def test_invalid_luggage_type_returns_error():
    data = {
        "destination": "Paris",
        "luggage_type": "suitcase-with-wheels",
        "start_date": "2026-06-01",
        "end_date": "2026-06-05"
    }
    trip_data, error = validate_data(data)

    assert trip_data is None
    assert error == "Luggage type must be checked, carry-on or backpack"


def test_luggage_type_is_normalised_to_lowercase():
    data = {
        "destination": "Paris",
        "luggage_type": "Carry-On",
        "start_date": "2026-06-01",
        "end_date": "2026-06-05"
    }
    trip_data, error = validate_data(data)

    assert error is None
    assert trip_data["luggage_type"] == "carry-on"


def test_invalid_date_format_returns_error():
    data = {
        "destination": "Paris",
        "luggage_type": "checked",
        "start_date": "01/06/2026",
        "end_date": "05/06/2026"
    }
    trip_data, error = validate_data(data)

    assert trip_data is None
    assert error == "Invalid date format. Please use YYYY-MM-DD"


def test_end_date_before_start_date_returns_error():
    data = {
        "destination": "Paris",
        "luggage_type": "checked",
        "start_date": "2026-06-10",
        "end_date": "2026-06-05"
    }
    trip_data, error = validate_data(data)

    assert trip_data is None
    assert error == "End date can't be before start date"


def test_same_start_and_end_date_is_valid():
    data = {
        "destination": "Paris",
        "luggage_type": "checked",
        "start_date": "2026-06-05",
        "end_date": "2026-06-05"
    }
    trip_data, error = validate_data(data)

    assert error is None
    assert trip_data["start_date"] == trip_data["end_date"]


# Validate activities

def test_valid_activities():
    data = {"activities": ["hiking", "swimming"]}
    activities, error = validate_activities(data)

    assert error is None
    assert activities == ["hiking", "swimming"]


def test_activities_are_stripped():
    data = {"activities": ["  hiking  "]}
    activities, error = validate_activities(data)

    assert error is None
    assert activities == ["hiking"]


def test_activities_not_a_list_returns_error():
    data = {"activities": "hiking"}
    activities, error = validate_activities(data)

    assert activities is None
    assert error == "Please provide the activities as a list"


def test_empty_activities_returns_error():
    data = {"activities": []}
    activities, error = validate_activities(data)

    assert activities is None
    assert error == "Please choose at least one activity"


def test_blank_activity_returns_error():
    data = {"activities": ["hiking", "   "]}
    activities, error = validate_activities(data)

    assert activities is None
    assert error == "Please use valid text format"
