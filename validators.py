import pytz
import logging

def validate_pricing(charger, charger_id):
    """
    Validates that the charger data includes 'pricing'.
    Returns a list of errors found.
    """
    errors = []
    if 'pricing' not in charger:
        error_message = f"Pricing object missing for charger {charger_id}"
        logging.warning(error_message)
        errors.append({
            'error_type': 'Pricing Missing',
            'message': error_message,
            'timestamp': 'N/A'
        })
    return errors

def validate_timezone_data(usage_data, charger_id):
    """
    Validates the timezone in the usage data.
    Returns a list of errors found.
    """
    errors = []
    timestamp = usage_data.get('timestamp', 'Unknown Timestamp')
    timezone = usage_data.get('timezone')
    if not timezone:
        error_message = f"Timezone missing in usage data at {timestamp}"
        logging.error(f"{error_message} for charger {charger_id}")
        errors.append({
            'error_type': 'Timezone Missing',
            'message': error_message,
            'timestamp': timestamp
        })
    elif not validate_timezone(timezone):
        error_message = f"Invalid timezone '{timezone}' in usage data at {timestamp}"
        logging.error(f"{error_message} for charger {charger_id}")
        errors.append({
            'error_type': 'Invalid Timezone',
            'message': error_message,
            'timestamp': timestamp
        })
    return errors

def validate_timezone(timezone_str):
    """
    Validate if the timezone string is a valid IANA timezone.
    """
    try:
        pytz.timezone(timezone_str)
        return True
    except pytz.UnknownTimeZoneError:
        return False

def validate_stalls_available(usage_data, charger_id):
    """
    Validates the stallsAvailable in the usage data.
    Returns a list of errors found.
    """
    errors = []
    timestamp = usage_data.get('timestamp', 'Unknown Timestamp')
    stalls_available_reported = usage_data.get('stallsAvailable')
    total_stalls = usage_data.get('totalStalls')
    stall_usage = usage_data.get('stallUsage', [])

    # Counting available stalls based on connector statuses
    stalls_available_count = 0
    for stall in stall_usage:
        connectors = stall.get('connectors', [])
        stall_available = any(connector.get('status') == 0 for connector in connectors)
        if stall_available:
            stalls_available_count += 1

    if stalls_available_reported != stalls_available_count:
        error_message = (
            f"Stalls available mismatch at {timestamp}: "
            f"Reported {stalls_available_reported}, Calculated {stalls_available_count}"
        )
        logging.error(f"{error_message} for charger {charger_id}")
        errors.append({
            'error_type': 'Stalls Available Mismatch',
            'message': error_message,
            'timestamp': timestamp
        })

    # Validating total stalls
    if total_stalls != len(stall_usage):
        error_message = (
            f"Total stalls mismatch at {timestamp}: "
            f"Reported {total_stalls}, Actual {len(stall_usage)}"
        )
        logging.error(f"{error_message} for charger {charger_id}")
        errors.append({
            'error_type': 'Total Stalls Mismatch',
            'message': error_message,
            'timestamp': timestamp
        })

    # Ensuring totalStalls = stallsAvailable + stallsNotAvailable
    stalls_not_available = total_stalls - stalls_available_reported
    calculated_total_stalls = stalls_available_reported + stalls_not_available
    if total_stalls != calculated_total_stalls:
        error_message = (
            f"Total stalls calculation error at {timestamp}: "
            f"Expected {total_stalls}, Calculated {calculated_total_stalls}"
        )
        logging.error(f"{error_message} for charger {charger_id}")
        errors.append({
            'error_type': 'Total Stalls Calculation Error',
            'message': error_message,
            'timestamp': timestamp
        })

    return errors
