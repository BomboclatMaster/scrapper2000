# scrapper2000

![scrapthat](https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExcnI1ZnYxYTV3bzBxdnZsd2VsbHF4NzJ6M3R5eWpiaXNmMmtieTlndyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/1xmCuRdZFAb5dskN1S/giphy.gif)

# Claim Generator

## Overview

The `claimgenerator.py` script generates professional medical bill PDFs for both legitimate and fraudulent claims. It uses the Faker library to generate fake patient data and the ReportLab library to create the PDF documents. The script also includes a progress bar to track the generation process.

## Features

- Generates medical bill PDFs with dynamic billing details.
- Supports both legitimate and fraudulent claims.
- Uses Faker to generate fake patient data.
- Includes a progress bar to track the generation process.
- Logs the generation process to a file.

## Prerequisites

- Python 3.x
- Required Python packages:
  - `reportlab`
  - `Pillow`
  - `concurrent.futures`
  - `datetime`
  - `typing`
  - `faker`
  - `tqdm`

## Installation

1. Clone the repository or download the `claimgenerator.py` script.
2. Install the required Python packages using pip:

    ```bash
    pip install reportlab Pillow faker tqdm
    ```

## Usage

1. Ensure the necessary directories exist:

    - `logos`: Directory to store generated logos.
    - `output`: Directory to store generated PDF files.

2. Prepare the input data files:

    - `hospitals_and_clinics.csv`: CSV file containing clinic information.
    - `doctors_and_specialists_list.csv`: CSV file containing doctor information.
    - `specialities_diseases.json`: JSON file mapping specialties to diseases.
    - `disease_consultation.json`: JSON file containing billing items for each diagnosis.

3. Run the `claimgenerator.py` script:

    ```bash
    python claimgenerator.py
    ```

4. The script will generate the specified number of legitimate and fraudulent claims and save them as PDF files in the `output` directory. The progress of the generation process will be displayed using a progress bar.

## Configuration

- The number of legitimate and fraudulent claims to generate can be configured in the script by modifying the `legitimate_count` and `fraudulent_count` variables.

## Logging

- The script logs the generation process to a file named `claim_generation.log`.

## Example

Here is an example of how to run the script:

```bash
python claimgenerator.py
```

The script will generate 50 legitimate and 50 fraudulent claims by default and save them as PDF files in the `output` directory.

## License

n o n e 😒
