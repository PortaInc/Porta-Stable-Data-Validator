# Porta Charging Data Validation Script

![Porta Logo](porta.png)
![Stable Auto Logo](stableauto.png)

This repository contains a Python script to validate the charging data provided by the Porta API. The script fetches charger usage data for all active Electrify America chargers in California and performs several validation checks to ensure data integrity for Stable. 

## Table of Contents

- [Introduction](#introduction)
- [System Requirements](#system-requirements)
- [Setup Instructions](#setup-instructions)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Create a Virtual Environment](#2-create-a-virtual-environment)
  - [3. Activate the Virtual Environment](#3-activate-the-virtual-environment)
  - [4. Install Dependencies](#4-install-dependencies)
- [Running the Script](#running-the-script)
- [Expected Output](#expected-output)
- [Contact Information](#contact-information)

## Introduction

This script is designed to:

- Retrieve a list of Electrify America charger IDs across California.
- Fetch usage data for each charger.
- Validate the data according to specified test cases.
- Provide a summary of the validation results.

## System Requirements

- **Operating System**: Linux, macOS, or Windows
- **Python Version**: Python 3.7 or higher
- **Pip**: Python package manager

## Setup Instructions

### 1. Clone the Repository

Clone this repository to your local machine:

```bash
git clone https://github.com/portainc/Porta-Stable-Data-Validator.git
cd your_project
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
```

## Running the Script

Execute the validation script:

```bash
python validate_chargers.py
```

## Expected Output

As the script runs, it will:

- Print progress messages for each charger, including the charger ID, name, and location.
- Introduce a 2-second delay after processing each charger to manage API load.
- Display errors found during validation, summarized per charger.
- At the end, a summary table will be printed, showing the results for all chargers.

### Sample Output

```
Processing charger ID: electrifyamerica-200046
Name: Ralphs 060 - Glendale, CA
Location: 1416 East Colorado Street, Glendale
Finished processing charger ID: electrifyamerica-200046
Usage Docs Processed: 6000
Total Errors Found: 10

Error Summary:
- Timezone Missing: 2 occurrences
  Example timestamps: 2024-11-18T13:20:16.148Z, 2024-11-18T13:40:16.089Z
- Stalls Available Mismatch: 5 occurrences
  Example timestamps: 2024-11-18T13:20:16.148Z, 2024-11-18T14:00:16.141Z
- Total Stalls Mismatch: 3 occurrences
  Example timestamps: 2024-11-18T14:20:16.150Z, 2024-11-18T14:40:16.152Z

...

Validation Summary:
+-------------------------------+-----------------------------+---------------------------------------+-----------------------+---------------+
| Charger ID                    | Name                        | Location                              |   Usage Docs Processed |   Total Errors |
+===============================+=============================+=======================================+=======================+===============+
| electrifyamerica-200046       | Ralphs 060 - Glendale, CA   | 1416 East Colorado Street, Glendale   |                  6000 |            10 |
+-------------------------------+-----------------------------+---------------------------------------+-----------------------+---------------+
| electrifyamerica-210016       | Target - Pasadena, CA       | 777 East Colorado Boulevard, Pasadena |                  6000 |             5 |
+-------------------------------+-----------------------------+---------------------------------------+-----------------------+---------------+
| ...                           | ...                         | ...                                   |                   ... |           ... |
+-------------------------------+-----------------------------+---------------------------------------+-----------------------+---------------+
```

## Contact Information

For any questions or issues, please contact:

- **Eliot Winchell**
- **Email**: eliot@portacharging.com
