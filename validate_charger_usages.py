import requests
import sys
import logging
import time
from collections import defaultdict
from tabulate import tabulate
from colorama import init, Fore, Style
from dotenv import load_dotenv
import os

from validators import (
    validate_pricing,
    validate_timezone_data,
    validate_stalls_available
)

# Initialize colorama for colorized terminal output
init(autoreset=True)

load_dotenv()

API_KEY = os.getenv('API_KEY')

if not API_KEY:
    print(Fore.RED + "Error: API_KEY not found in environment variables.")
    sys.exit(1)

logging.basicConfig(
    filename='validation.log',
    filemode='w',
    format='%(levelname)s:%(message)s',
    level=logging.INFO
)

def main():
    charger_ids_url = 'https://api.portacharging.com/v1/chargers/california/electrifyAmerica'

    headers = {
        'Authorization': f'Bearer {API_KEY}'
    }

    # Fetching all EA chargers in CA from Porta
    try:
        response = requests.get(charger_ids_url, headers=headers)
        response.raise_for_status()
    except requests.HTTPError as e:
        # Get the status code
        status_code = e.response.status_code if e.response else None
        error_message = e.response.text if e.response else str(e)

        if status_code == 401:
            print(Fore.RED + "Error: Unauthorized access. Please check your API key.")
        elif status_code == 403:
            print(Fore.RED + "Error: Forbidden. You do not have permission to access this resource.")
        else:
            print(Fore.RED + f"HTTP Error {status_code}: {error_message}")

        logging.error(f"Failed to fetch charger IDs: {e}")
        sys.exit(1)
    except requests.RequestException as e:
        print(Fore.RED + f"Error: Failed to fetch charger IDs. {str(e)}")
        logging.error(f"Failed to fetch charger IDs: {e}")
        sys.exit(1)

    charger_ids = response.json().get('chargerIds', [])
    if not charger_ids:
        logging.error("No charger IDs found in the response.")
        print(Fore.RED + "Error: No charger IDs found in the response.")
        sys.exit(1)

    overall_results = []

    for charger_id in charger_ids:
        usages_url = f'https://api.portacharging.com/v1/chargers/{charger_id}/usages'
        charger_errors = defaultdict(int)
        charger_error_details = []
        num_usage_docs = 0

        try:
            response = requests.get(usages_url, headers=headers)
            response.raise_for_status()
        except requests.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            error_message = e.response.text if e.response else str(e)

            if status_code == 401:
                print(Fore.RED + f"Error: Unauthorized access for charger {charger_id}. Please check your API key.")
            elif status_code == 403:
                print(Fore.RED + f"Error: Forbidden access for charger {charger_id}.")
            else:
                print(Fore.RED + f"HTTP Error {status_code} for charger {charger_id}: {error_message}")

            logging.error(f"Failed to fetch usages for {charger_id}: {e}")
            charger_errors['API Errors'] += 1
            overall_results.append({
                'Charger ID': charger_id,
                'Name': 'N/A',
                'Location': 'N/A',
                'Usage Docs Processed': num_usage_docs,
                'Total Errors': sum(charger_errors.values())
            })
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

        errors = validate_pricing(charger, charger_id)
        for error in errors:
            charger_errors[error['error_type']] += 1
            charger_error_details.append(error)

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

            errors = validate_timezone_data(usage_data, charger_id)
            for error in errors:
                charger_errors[error['error_type']] += 1
                charger_error_details.append(error)

            errors = validate_stalls_available(usage_data, charger_id)
            for error in errors:
                charger_errors[error['error_type']] += 1
                charger_error_details.append(error)

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
                # showing up to 5 to avoid cluttering the console
                example_errors = errors[:5]
                timestamps = [err['timestamp'] for err in example_errors]
                print(f"  Example timestamps: {', '.join(timestamps)}")
            print("\n")
        else:
            print(Fore.GREEN + "No errors found for this charger.\n")

        # added a delay to avoid overloading our API
        time.sleep(1)

    # summary table 
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
