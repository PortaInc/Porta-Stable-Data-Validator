import requests
import pytz
import sys
import logging

# Configure logging
logging.basicConfig(
    filename='validation.log',
    filemode='w',
    format='%(levelname)s:%(message)s',
    level=logging.INFO
)

def validate_timezone(timezone_str):
    """
    Validate if the timezone string is a valid IANA timezone.
    """
    try:
        pytz.timezone(timezone_str)
        return True
    except pytz.UnknownTimeZoneError:
        return False

def main():
    # Endpoint URLs
    charger_ids_url = 'https://api-stg.portacharging.com/v1/chargers/california/electrifyAmerica'

    # Fetch the list of charger IDs
    try:
        response = requests.get(charger_ids_url)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch charger IDs: {e}")
        sys.exit(1)

    charger_ids = response.json().get('chargerIds', [])
    if not charger_ids:
        logging.error("No charger IDs found in the response.")
        sys.exit(1)

    # Iterate over each charger ID
    for charger_id in charger_ids:
        usages_url = f'https://api-stg.portacharging.com/v1/chargers/{charger_id}/usages'
        try:
            response = requests.get(usages_url)
            response.raise_for_status()
        except requests.RequestException as e:
            logging.error(f"Failed to fetch usages for {charger_id}: {e}")
            continue  # Skip to the next charger ID

        data = response.json()

        # Test Case 3: Ensure 'charger' has 'pricing' object
        charger = data.get('charger', {})
        if 'pricing' not in charger:
            logging.warning(f"Pricing object missing for charger {charger_id}")

        usage_data_list = data.get('usageData', [])
        if not usage_data_list:
            logging.warning(f"No usage data found for charger {charger_id}")
            continue  # Skip to the next charger ID

        # Iterate over each usage document
        for usage_data in usage_data_list:
            timestamp = usage_data.get('timestamp', 'Unknown Timestamp')

            # Test Case 1: Validate timezone
            timezone = usage_data.get('timezone')
            if not timezone:
                logging.error(f"Timezone missing in usage data for charger {charger_id} at {timestamp}")
            elif not validate_timezone(timezone):
                logging.error(f"Invalid timezone '{timezone}' in usage data for charger {charger_id} at {timestamp}")

            # Test Case 2: Validate stallsAvailable
            stalls_available_reported = usage_data.get('stallsAvailable')
            total_stalls = usage_data.get('totalStalls')
            stall_usage = usage_data.get('stallUsage', [])

            # Count available stalls based on connector statuses
            stalls_available_count = 0
            for stall in stall_usage:
                connectors = stall.get('connectors', [])
                for connector in connectors:
                    if connector.get('status') == 0:
                        stalls_available_count += 1

            if stalls_available_reported != stalls_available_count:
                logging.error(
                    f"Stalls available mismatch for charger {charger_id} at {timestamp}: "
                    f"Reported {stalls_available_reported}, Calculated {stalls_available_count}"
                )

            # Validate total stalls
            if total_stalls != len(stall_usage):
                logging.error(
                    f"Total stalls mismatch for charger {charger_id} at {timestamp}: "
                    f"Reported {total_stalls}, Actual {len(stall_usage)}"
                )

            # Ensure totalStalls = stallsAvailable + stallsNotAvailable
            stalls_not_available = total_stalls - stalls_available_reported
            calculated_total_stalls = stalls_available_reported + stalls_not_available
            if total_stalls != calculated_total_stalls:
                logging.error(
                    f"Total stalls calculation error for charger {charger_id} at {timestamp}: "
                    f"Expected {total_stalls}, Calculated {calculated_total_stalls}"
                )

if __name__ == '__main__':
    main()

