from datetime import datetime

# Validate basic trip data
def validate_data(data):
    destination = data.get("destination", "").strip()
    luggage_type = data.get("luggage_type", "").strip()
    start_date = data.get("start_date", "").strip()
    end_date = data.get("end_date", "").strip()

    if not destination or not luggage_type or not start_date or not end_date:
        return None, "Please fill in all the information"

    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        return None, "Invalid date format. Please use YYYY-MM-DD"

    if end_date < start_date:
        return None, "End date can't be before start date"

    trip_data = {
        "destination": destination,
        "luggage_type": luggage_type,
        "start_date": start_date,
        "end_date": end_date
    }

    return trip_data, None

# Validate activities data
def validate_activities(data):
    if not isinstance(data, dict):
        return None, "Invalid input"

    activities = data.get("activities")

    if not isinstance(activities, list):
        return None, "Please provide the activities as a list"

    if len(activities) == 0:
        return None, "Please choose at least one activity"

    cleaned_activities = []

    for activity in activities:
        if not isinstance(activity, str) or not activity.strip():
            return None, "Please use valid text format"

        cleaned_activities.append(activity.strip())

    return cleaned_activities, None