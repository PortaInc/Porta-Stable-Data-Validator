import requests
import sys
import logging
import time
import argparse
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

def fetch_charger_ids(region='unitedStates'):
    """
    Fetch charger IDs based on the specified region.
    
    Args:
        region (str): Either 'unitedStates' or 'california'
    
    Returns:
        list: List of charger IDs
    """
    base_url = 'https://api.portacharging.com/v1/chargers'
    url = f"{base_url}/{'california' if region == 'california' else 'unitedStates'}/electrifyAmerica"

    headers = {
        'Authorization': f'Bearer {API_KEY}'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.HTTPError as e:
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
    
    return charger_ids

def process_charger(charger_id, headers):
    """
    Process a single charger and return its results.
    """
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

        print(Fore.RED + f"HTTP Error {status_code} for charger {charger_id}: {error_message}")
        logging.error(f"Failed to fetch usages for {charger_id}: {e}")
        return {
            'Charger ID': charger_id,
            'Name': 'N/A',
            'Location': 'N/A',
            'Usage Docs Processed': 0,
            'Total Errors': 1,
            'Error Details': [{'error_type': 'API Error', 'timestamp': 'N/A'}]
        }

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

    # Validate pricing
    errors = validate_pricing(charger, charger_id)
    for error in errors:
        charger_errors[error['error_type']] += 1
        charger_error_details.append(error)

    usage_data_list = data.get('usageData', [])
    if not usage_data_list:
        logging.warning(f"No usage data found for charger {charger_id}")
        print(Fore.YELLOW + f"No usage data found for charger {charger_id}.\n")
        return {
            'Charger ID': charger_id,
            'Name': charger_name,
            'Location': location_str,
            'Usage Docs Processed': 0,
            'Total Errors': sum(charger_errors.values()),
            'Error Details': charger_error_details
        }

    for usage_data in usage_data_list:
        num_usage_docs += 1

        for validator in [validate_timezone_data, validate_stalls_available]:
            errors = validator(usage_data, charger_id)
            for error in errors:
                charger_errors[error['error_type']] += 1
                charger_error_details.append(error)

    return {
        'Charger ID': charger_id,
        'Name': charger_name,
        'Location': location_str,
        'Usage Docs Processed': num_usage_docs,
        'Total Errors': sum(charger_errors.values()),
        'Error Details': charger_error_details
    }

def main():
    parser = argparse.ArgumentParser(description='Validate Electrify America charger data')
    parser.add_argument('--region', choices=['us', 'california'], default='us',
                      help='Region to analyze (us or california)')
    parser.add_argument('--charger-id', type=str,
                      help='Specific charger ID to analyze (optional)')
    args = parser.parse_args()

    headers = {'Authorization': f'Bearer {API_KEY}'}
    overall_results = []

    if args.charger_id:
        print(f"Analyzing single charger ID: {args.charger_id}")
        result = process_charger(args.charger_id, headers)
        overall_results.append(result)
    else:
        print(f"Fetching Electrify America charger data for {args.region.upper()}...")
        charger_ids = fetch_charger_ids(args.region)
        for charger_id in charger_ids:
            result = process_charger(charger_id, headers)
            overall_results.append(result)
            time.sleep(0.25)

    for result in overall_results:
        print(Fore.GREEN + f"Finished processing charger ID: {result['Charger ID']}")
        print(f"Usage Docs Processed: {result['Usage Docs Processed']}")
        print(f"Total Errors Found: {result['Total Errors']}")

        if result['Error Details']:
            print(Fore.RED + "\nError Summary:")
            error_summary = defaultdict(list)
            for error in result['Error Details']:
                error_summary[error['error_type']].append(error)

            for error_type, errors in error_summary.items():
                print(Fore.RED + f"- {error_type}: {len(errors)} occurrences")
                example_errors = errors[:5]  # Show up to 5 examples
                timestamps = [err['timestamp'] for err in example_errors]
                print(f"  Example timestamps: {', '.join(timestamps)}")
            print("\n")
        else:
            print(Fore.GREEN + "No errors found for this charger.\n")

    print("\nValidation Summary:")
    headers = ['Charger ID', 'Name', 'Location', 'Usage Docs Processed', 'Total Errors']
    table = [[result[h] for h in headers] for result in overall_results]
    print(Fore.BLUE + Style.BRIGHT + tabulate(table, headers=headers, tablefmt='grid'))

if __name__ == '__main__':
    main()