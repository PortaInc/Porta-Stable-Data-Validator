import requests
import pytz
import sys
import logging
import time
from collections import defaultdict
from tabulate import tabulate
from colorama import init, Fore, Style

# Easier to read output in the terminal
init(autoreset=True)

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
    charger_ids_url = 'https://api-stg.portacharging.com/v1/chargers/california/electrifyAmerica'

    # fetching all EA chargers in California from Porta
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

    overall_results = []

    for charger_id in charger_ids:
        usages_url = f'https://api-stg.portacharging.com/v1/chargers/{charger_id}/usages'
        charger_errors = defaultdict(int)
        charger_error_details = []
        num_usage_docs = 0

        try:
            response = requests.get(usages_url)
            response.raise_for_status()
        except requests.RequestException as e:
            logging.error(f"Failed to fetch usages for {charger_id}: {e}")
            charger_errors['API Errors'] += 1
            overall_results.append({
                'Charger ID': charger_id,
                'Name': 'N/A',
                'Location': 'N/A',
                'Usage Docs Processed': num_usage_docs,
                'Total Errors': sum(charger_errors.values())
            })
            print(Fore.RED + f"Processing charger ID: {charger_id} - Failed to fetch data.\n")
            time.sleep(1)
            continue

        data = response.json()

        charger = data.get('charger', {})
        charger_name = charger.get('name', 'Unknown Name')

        address = charger.get('address', {})
        full_thoroughfare = address.get('fullThoroughfare', 'Unknown Address')
        locality = address.get('locality', 'Unknown Locality')
        location_str = f"{full_thoroughfare}, {locality}"

        print(Style.BRIGHT + f"Processing charger ID: {charger_id}")
        print(f"Name: {charger_name}")
        print(f"Location: {location_str}")

        # Third test case
        if 'pricing' not in charger:
            error_message = f"Pricing object missing for charger {charger_id}"
            logging.warning(error_message)
            charger_errors['Pricing Missing'] += 1
            charger_error_details.append({
                'error_type': 'Pricing Missing',
                'message': error_message,
                'timestamp': 'N/A'
            })

        usage_data_list = data.get('usageData', [])
        if not usage_data_list:
            logging.warning(f"No usage data found for charger {charger_id}")
            overall_results.append({
                'Charger ID': charger_id,
                'Name': charger_name,
                'Location': location_str,
                'Usage Docs Processed': num_usage_docs,
                'Total Errors': sum(charger_errors.values())
            })
            print(Fore.YELLOW + f"No usage data found for charger {charger_id}.\n")
            time.sleep(1)
            continue  

        for usage_data in usage_data_list:
            num_usage_docs += 1
            timestamp = usage_data.get('timestamp', 'Unknown Timestamp')

            # First test case: validating timezone
            timezone = usage_data.get('timezone')
            if not timezone:
                error_message = f"Timezone missing in usage data at {timestamp}"
                logging.error(f"{error_message} for charger {charger_id}")
                charger_errors['Timezone Missing'] += 1
                charger_error_details.append({
                    'error_type': 'Timezone Missing',
                    'message': error_message,
                    'timestamp': timestamp
                })
            elif not validate_timezone(timezone):
                error_message = f"Invalid timezone '{timezone}' in usage data at {timestamp}"
                logging.error(f"{error_message} for charger {charger_id}")
                charger_errors['Invalid Timezone'] += 1
                charger_error_details.append({
                    'error_type': 'Invalid Timezone',
                    'message': error_message,
                    'timestamp': timestamp
                })

            # Test Case 2: validating stallsAvailable
            stalls_available_reported = usage_data.get('stallsAvailable')
            total_stalls = usage_data.get('totalStalls')
            stall_usage = usage_data.get('stallUsage', [])

            # cunting available stalls based on connector statuses
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
                charger_errors['Stalls Available Mismatch'] += 1
                charger_error_details.append({
                    'error_type': 'Stalls Available Mismatch',
                    'message': error_message,
                    'timestamp': timestamp
                })

            # validating total stalls
            if total_stalls != len(stall_usage):
                error_message = (
                    f"Total stalls mismatch at {timestamp}: "
                    f"Reported {total_stalls}, Actual {len(stall_usage)}"
                )
                logging.error(f"{error_message} for charger {charger_id}")
                charger_errors['Total Stalls Mismatch'] += 1
                charger_error_details.append({
                    'error_type': 'Total Stalls Mismatch',
                    'message': error_message,
                    'timestamp': timestamp
                })

            # Here we're ensuring that totalStalls = stallsAvailable + stallsNotAvailable
            stalls_not_available = total_stalls - stalls_available_reported
            calculated_total_stalls = stalls_available_reported + stalls_not_available
            if total_stalls != calculated_total_stalls:
                error_message = (
                    f"Total stalls calculation error at {timestamp}: "
                    f"Expected {total_stalls}, Calculated {calculated_total_stalls}"
                )
                logging.error(f"{error_message} for charger {charger_id}")
                charger_errors['Total Stalls Calculation Error'] += 1
                charger_error_details.append({
                    'error_type': 'Total Stalls Calculation Error',
                    'message': error_message,
                    'timestamp': timestamp
                })

        overall_results.append({
            'Charger ID': charger_id,
            'Name': charger_name,
            'Location': location_str,
            'Usage Docs Processed': num_usage_docs,
            'Total Errors': sum(charger_errors.values())
        })

        print(Fore.GREEN + f"Finished processing charger ID: {charger_id}")
        print(f"Usage Docs Processed: {num_usage_docs}")
        print(f"Total Errors Found: {sum(charger_errors.values())}")

        if charger_error_details:
            print(Fore.RED + "\nError Summary:")
            error_summary = defaultdict(list)
            for error in charger_error_details:
                error_summary[error['error_type']].append(error)

            for error_type, errors in error_summary.items():
                print(Fore.RED + f"- {error_type}: {len(errors)} occurrences")
                # Show up to 5 example timestamps
                example_errors = errors[:5]
                timestamps = [err['timestamp'] for err in example_errors]
                print(f"  Example timestamps: {', '.join(timestamps)}")
            print("\n")
        else:
            print(Fore.GREEN + "No errors found for this charger.\n")

        # added a delay so we don't DDOS our API 
        time.sleep(1)

    # summary table after all of the chargers have been processed
    print("\nValidation Summary:")
    headers = [
        'Charger ID',
        'Name',
        'Location',
        'Usage Docs Processed',
        'Total Errors'
    ]
    table = [ [result[h] for h in headers] for result in overall_results ]
    print(Fore.BLUE + Style.BRIGHT + tabulate(table, headers=headers, tablefmt='grid'))

if __name__ == '__main__':
    main()
