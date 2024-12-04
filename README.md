# Porta Charging Data Validation Script

![Porta // Stable Logos](banner.png)

This repository contains a Python script to validate the charging data provided by the Porta API. The script can fetch and validate usage data for Electrify America chargers across the United States, California specifically, or individual chargers.

## Table of Contents

- [Introduction](#introduction)
- [System Requirements](#system-requirements)
- [Setup Instructions](#setup-instructions)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Create a Virtual Environment](#2-create-a-virtual-environment)
  - [3. Activate the Virtual Environment](#3-activate-the-virtual-environment)
  - [4. Install Dependencies](#4-install-dependencies)
  - [5. Set Up the API Key](#5-set-up-the-api-key)
- [Running the Script](#running-the-script)
- [Expected Output](#expected-output)
- [Contact Information](#contact-information)

## Introduction

This script is designed to:

- Retrieve Electrify America charger data based on specified criteria (US-wide, California-only, or single charger)
- Fetch usage data for each charger
- Validate the data according to specified test cases
- Provide a summary of the validation results

## System Requirements

- **Operating System**: Linux, macOS, or Windows
- **Python Version**: Python 3.7 or higher
- **Pip**: Python package manager

## Setup Instructions

### 1. Clone the Repository

Clone this repository to your local machine:

```bash
git clone https://github.com/PortaInc/Porta-Stable-Data-Validator.git
cd Porta-Stable-Data-Validator
```

### 2. Create a Virtual Environment

Create a virtual environment to manage dependencies:

```bash
python3 -m venv venv
```

### 3. Activate the Virtual Environment

- **On macOS/Linux**:

  ```bash
  source venv/bin/activate
  ```

- **On Windows**:

  ```bash
  venv\Scripts\activate
  ```

### 4. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

The `requirements.txt` includes:

```txt
requests==2.31.0
pytz==2023.3
tabulate==0.9.0
colorama==0.4.6
python-dotenv==1.0.0
```

### 5. Set Up the API Key

The script requires an API key to authenticate requests to the Porta Charging API. The API key should be stored in a `.env` file in the root directory of the project.

1. **Create a `.env` file** in the root directory:

   ```bash
   touch .env
   ```

2. **Add your API key** to the `.env` file:

   ```env
   API_KEY=<Put API key from Eliot here>
   ```

## Running the Script

The script can be run in three different modes:

1. **Analyze all US chargers** (default):
```bash
python3 validate_charger_usages.py
# or explicitly specify US
python3 validate_charger_usages.py --region us
```

2. **Analyze California-specific chargers**:
```bash
python3 validate_charger_usages.py --region california
```

3. **Analyze a specific charger by ID**:
```bash
python3 validate_charger_usages.py --charger-id electrifyamerica-100099
```

**Note**: Ensure the virtual environment is activated and the `.env` file is properly set up before running the script.

## Expected Output

As the script runs, it will:

- Print progress messages for each charger, including the charger ID, name, and location
- Introduce a brief delay between chargers to manage API load
- Display errors found during validation, summarized per charger
- At the end, a summary table will be printed, showing the results for all chargers

### Sample Output

```
Processing charger ID: electrifyamerica-100099
Name: Walmart 3847 - Mesquite, NV
Location: 1120 West Pioneer Boulevard, Mesquite
Finished processing charger ID: electrifyamerica-100099
Usage Docs Processed: 6152
Total Errors Found: 3070

Error Summary:
- Timezone Missing: 3070 occurrences
  Example timestamps: 2024-08-19T17:51:56.182Z, 2024-08-19T18:11:56.129Z, 2024-08-19T18:31:56.069Z, 2024-08-19T18:51:56.063Z, 2024-08-19T19:11:56.096Z

...

Validation Summary:
+-------------------------------+-----------------------------+---------------------------------------+-----------------------+---------------+
| Charger ID                    | Name                        | Location                              |   Usage Docs Processed |   Total Errors |
+===============================+=============================+=======================================+=======================+===============+
| electrifyamerica-200046       | Ralphs 060 - Glendale, CA   | 1416 East Colorado Street, Glendale   |                  1000 |             1 |
+-------------------------------+-----------------------------+---------------------------------------+-----------------------+---------------+
| electrifyamerica-210016       | Target - Pasadena, CA       | 777 East Colorado Boulevard, Pasadena |                  1000 |             0 |
+-------------------------------+-----------------------------+---------------------------------------+-----------------------+---------------+
| ...                           | ...                         | ...                                   |                   ... |           ... |
+-------------------------------+-----------------------------+---------------------------------------+-----------------------+---------------+
```

## Additional Notes

- **Security**: The API key is stored securely in the `.env` file and is not committed to the repository, following best practices
- **Environment Variables**: You can set the `API_KEY` as an environment variable in your system if you prefer not to use a `.env` file
- **Error Handling**: The script will exit if the `API_KEY` is not found, preventing unauthorized requests

## Contact Information

For any questions or issues, please contact:

- **Eliot Winchell**
- **Email**: eliot@portacharging.com