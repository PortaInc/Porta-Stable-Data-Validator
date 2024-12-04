import pytz
import logging

def validate_pricing(charger, charger_id):
    """
    Validates that the charger data includes 'pricing'
    Returns a list of errors found
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
    Validates the timezone in the usage data
    Returns a list of errors found
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
    Validate if the timezone string is a valid IANA timezone
    """
    try:
        pytz.timezone(timezone_str)
        return True
    except pytz.UnknownTimeZoneError:
        return False

def validate_stalls_available(usage_data, charger_id):
    """
    Validates the stallsAvailable in the usage data, accounting for connectors with status -2
    Returns a list of errors found
    """
    errors = []
    timestamp = usage_data.get('timestamp', 'Unknown Timestamp')
    stalls_available_reported = usage_data.get('stallsAvailable')
    total_stalls_reported = usage_data.get('totalStalls')
    stall_usage = usage_data.get('stallUsage', [])

    total_stalls_calculated = 0
    stalls_available_calculated = 0

    # If the connector status is -2, then we failed to fetch their API
    all_connectors_status_minus2 = True

    for stall in stall_usage:
        connectors = stall.get('connectors', [])
        stall_has_valid_status = False
        stall_available = False
        for connector in connectors:
            status = connector.get('status')
            if status != -2:
                all_connectors_status_minus2 = False
                stall_has_valid_status = True
                if status == 0:
                    stall_available = True
                break  # Exit loop since we have valid status for this connector
        if stall_has_valid_status:
            total_stalls_calculated += 1
            if stall_available:
                stalls_available_calculated += 1

    if all_connectors_status_minus2:
        # all connectors have status -2, data unavailable, skip validation
        logging.info(f"All connectors have status -2 at {timestamp} for charger {charger_id}, skipping stallsAvailable validation")
        return errors 

    if stalls_available_reported != stalls_available_calculated:
        error_message = (
            f"Stalls available mismatch at {timestamp}: "
            f"Reported {stalls_available_reported}, Calculated {stalls_available_calculated}"
        )
        logging.error(f"{error_message} for charger {charger_id}")
        errors.append({
            'error_type': 'Stalls Available Mismatch',
            'message': error_message,
            'timestamp': timestamp
        })

    if total_stalls_reported != total_stalls_calculated:
        error_message = (
            f"Total stalls mismatch at {timestamp}: "
            f"Reported {total_stalls_reported}, Calculated {total_stalls_calculated}"
        )
        logging.error(f"{error_message} for charger {charger_id}")
        errors.append({
            'error_type': 'Total Stalls Mismatch',
            'message': error_message,
            'timestamp': timestamp
        })

    stalls_not_available_reported = total_stalls_reported - stalls_available_reported
    stalls_not_available_calculated = total_stalls_calculated - stalls_available_calculated

    if stalls_not_available_reported != stalls_not_available_calculated:
        error_message = (
            f"Stalls not available mismatch at {timestamp}: "
            f"Reported {stalls_not_available_reported}, Calculated {stalls_not_available_calculated}"
        )
        logging.error(f"{error_message} for charger {charger_id}")
        errors.append({
            'error_type': 'Stalls Not Available Mismatch',
            'message': error_message,
            'timestamp': timestamp
        })

    # Ensure totalStalls = stallsAvailable + stallsNotAvailable
    if total_stalls_reported != stalls_available_reported + stalls_not_available_reported:
        error_message = (
            f"Total stalls calculation error at {timestamp}: "
            f"Reported totalStalls ({total_stalls_reported}) does not equal stallsAvailable ({stalls_available_reported}) "
            f"+ stallsNotAvailable ({stalls_not_available_reported})"
        )
        logging.error(f"{error_message} for charger {charger_id}")
        errors.append({
            'error_type': 'Total Stalls Calculation Error',
            'message': error_message,
            'timestamp': timestamp
        })

    return errors